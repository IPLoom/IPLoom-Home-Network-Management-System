from fastapi import APIRouter, HTTPException, BackgroundTasks
from app.services.integrations.deco import DecoClient
from app.models.deco import DecoConfig, DecoVerifyRequest
from app.core.db import get_connection, commit
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/config")
def get_config():
    conn = get_connection()
    try:
        row = conn.execute("SELECT config FROM integrations WHERE name = 'deco'").fetchone()

        # Fetch verified status from config table
        v_row = conn.execute("SELECT value FROM config WHERE key = 'deco_verified'").fetchone()
        verified = (v_row[0] == "true") if v_row else False

        if row:
            conf = json.loads(row[0])
            conf["verified"] = verified

            # Mask password
            if conf.get("password"):
                conf["password"] = "*****"
            return conf

        return {"verified": verified}
    finally:
        conn.close()



@router.post("/config")
def save_config(config: DecoConfig):
    conn = get_connection()
    try:
        row = conn.execute("SELECT config FROM integrations WHERE name = 'deco'").fetchone()
        existing = json.loads(row[0]) if row else {}

        new_conf = config.dict()
        if config.password is None or config.password == "*****":
            new_conf["password"] = existing.get("password")

        # Merge existing state fields
        for key in ["last_sync", "last_run"]:
            if key in existing and key not in new_conf:
                new_conf[key] = existing[key]

        # Auto-verify on save
        verified = False
        if new_conf.get("host") and new_conf.get("password") and new_conf.get("enabled", True):
            try:
                client = DecoClient(new_conf["host"], new_conf["password"])
                client.login()
                verified = True
            except Exception as e:
                logger.warning(f"Deco verification failed during save: {e}")
                verified = False

        # Save main config
        conn.execute(
            "INSERT OR REPLACE INTO integrations (name, config) VALUES ('deco', ?)",
            [json.dumps(new_conf)],
        )

        # Save verified status to config table
        conn.execute(
            "INSERT OR REPLACE INTO config (key, value) VALUES ('deco_verified', ?)",
            ["true" if verified else "false"],
        )

        conn.commit()

        # Broadcast update
        from app.core.notifications import manager
        manager.broadcast_sync({
            "type": "integration_status",
            "integration": "deco",
            "data": {"verified": verified},
        })

        return {"status": "saved", "verified": verified}
    finally:
        conn.close()


@router.post("/verify")
def verify_connection(creds: DecoVerifyRequest):
    try:
        client = DecoClient(creds.host, creds.password)
        client.verify()

        # Update verified status in config table
        conn = get_connection()
        try:
            conn.execute(
                "INSERT OR REPLACE INTO config (key, value) VALUES ('deco_verified', 'true')"
            )
            conn.commit()

            # Broadcast update
            from app.core.notifications import manager
            manager.broadcast_sync({
                "type": "integration_status",
                "integration": "deco",
                "data": {"verified": True},
            })
        finally:
            conn.close()

        return {"status": "success", "message": "Connected to Deco successfully", "verified": True}
    except Exception as e:
        # On failure, update DB to false
        conn = get_connection()
        try:
            conn.execute(
                "INSERT OR REPLACE INTO config (key, value) VALUES ('deco_verified', 'false')"
            )
            conn.commit()

            from app.core.notifications import manager
            manager.broadcast_sync({
                "type": "integration_status",
                "integration": "deco",
                "data": {"verified": False, "error": str(e)},
            })
        finally:
            conn.close()
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/sync")
async def trigger_sync(background_tasks: BackgroundTasks):
    conn = get_connection()
    try:
        row = conn.execute("SELECT config FROM integrations WHERE name = 'deco'").fetchone()
        if not row:
            raise HTTPException(status_code=400, detail="Deco not configured")

        # Check verified status
        v_row = conn.execute("SELECT value FROM config WHERE key = 'deco_verified'").fetchone()
        is_verified = (v_row[0] == "true") if v_row else False

        if not is_verified:
            raise HTTPException(
                status_code=400,
                detail="Configuration not verified. Please save or test connection first.",
            )

        conf = json.loads(row[0])
        client = DecoClient(conf["host"], conf["password"])
        background_tasks.add_task(client.sync, force=True)
        return {"status": "queued", "message": "Deco sync started in background"}
    finally:
        conn.close()


@router.get("/signal-history/{device_id}")
def get_signal_history(device_id: str, hours: int = 24):
    """Get RSSI signal history for a device from wifi_signal_history."""
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT rssi, band, mesh_node, source, timestamp
            FROM wifi_signal_history
            WHERE device_id = ?
            AND timestamp >= CURRENT_TIMESTAMP - (CAST(? AS INTEGER) * INTERVAL '1 hour')
            ORDER BY timestamp ASC
            """,
            [device_id, hours],
        ).fetchall()

        return [
            {
                "rssi": r[0],
                "band": r[1],
                "mesh_node": r[2],
                "source": r[3],
                "timestamp": r[4].isoformat() if r[4] else None,
            }
            for r in rows
        ]
    except Exception as e:
        logger.error(f"Error fetching signal history: {e}")
        return []
    finally:
        conn.close()


@router.get("/data")
def get_deco_data():
    conn = get_connection()
    try:
        # Check config & verified
        v_row = conn.execute("SELECT value FROM config WHERE key = 'deco_verified'").fetchone()
        verified = (v_row[0] == "true") if v_row else False

        c_row = conn.execute("SELECT config FROM integrations WHERE name = 'deco'").fetchone()
        config = json.loads(c_row[0]) if c_row else {}

        if not verified or not config.get("enabled", True):
            return {
                "verified": verified,
                "enabled": config.get("enabled", False),
                "nodes": [],
                "clients": []
            }

        # Fetch devices that are Deco nodes or clients synced by Deco
        rows = conn.execute(
            """
            SELECT d.id, d.ip, d.mac, d.name, d.display_name, d.status, d.attributes, d.last_seen, s.attributes, d.icon,
                   d.is_trusted, d.ip_type, d.is_blocked, d.brand_icon, d.device_type, d.vendor
            FROM devices d
            LEFT JOIN device_discovery_sources s ON d.id = s.device_id AND s.source = 'deco'
            WHERE s.device_id IS NOT NULL
               OR json_extract_string(d.attributes, '$.deco_role') IS NOT NULL
            """
        ).fetchall()

        nodes = []
        clients = []

        for r in rows:
            dev_id, ip, mac, name, display_name, status, attrs_str, last_seen, src_attrs_str, icon, is_trusted, ip_type, is_blocked, brand_icon, device_type, vendor = r
            attrs = {}
            if attrs_str:
                try:
                    attrs = json.loads(attrs_str)
                except:
                    pass
            if src_attrs_str:
                try:
                    attrs.update(json.loads(src_attrs_str))
                except:
                    pass

            item = {
                "id": dev_id,
                "ip": ip,
                "mac": mac,
                "name": display_name or name or mac or "Unknown",
                "display_name": display_name,
                "status": status,
                "icon": icon,
                "last_seen": last_seen.isoformat() if last_seen else None,
                "attributes": attrs,
                "is_trusted": bool(is_trusted),
                "ip_type": ip_type,
                "is_blocked": bool(is_blocked),
                "brand_icon": brand_icon,
                "device_type": device_type,
                "vendor": vendor
            }

            if attrs.get("deco_role"):
                nodes.append(item)
            else:
                clients.append(item)

        return {
            "verified": verified,
            "enabled": config.get("enabled", True),
            "last_run": config.get("last_run"),
            "nodes": nodes,
            "clients": clients
        }
    except Exception as e:
        logger.error(f"Error fetching Deco integration data: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

