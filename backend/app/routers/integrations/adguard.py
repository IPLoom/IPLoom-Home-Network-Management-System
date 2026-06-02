from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
from app.services.integrations.adguard import AdguardClient
from app.core.db import get_connection, commit
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class AdguardConfig(BaseModel):
    url: str
    username: Optional[str] = None
    password: Optional[str] = None
    interval: int = 5
    enabled: bool = True

@router.get("/config")
def get_config():
    conn = get_connection()
    try:
        row = conn.execute("SELECT config FROM integrations WHERE name = 'adguard'").fetchone()
        if not row:
            return None
        config = json.loads(row[0])
        # Mask password
        if config.get("password"):
            config["password"] = "******"
        
        # Check if actually working
        verified = config.get("verified", False)
        return {**config, "verified": verified}
    finally:
        conn.close()

from datetime import datetime, timezone
from app.core.date_utils import now as utc_now
@router.post("/config")
def save_config(config: AdguardConfig):
    conn = get_connection()
    try:
        # Fetch existing to merge
        row = conn.execute("SELECT config FROM integrations WHERE name = 'adguard'").fetchone()
        existing = json.loads(row[0]) if row else {}
        
        # Store
        data = config.dict()
        if config.password is None or config.password == "******":
            data["password"] = existing.get("password")

        # Merge existing state fields (last_sync, last_run, etc.)
        for key in ["last_sync", "last_run", "verified", "last_check", "enabled"]:
            if key in existing and key not in data:
                data[key] = existing[key]

        # Verify immediately
        try:
            client = AdguardClient(data["url"], data["username"], data["password"])
            client.test_connection()
            data["verified"] = True
            data["last_check"] = utc_now().isoformat()
        except Exception as e:
            logger.warning(f"Adguard verification failed during save: {e}")
            data["verified"] = False
            data["error"] = str(e)
            
        conn.execute(
            "INSERT OR REPLACE INTO integrations (name, config) VALUES (?, ?)",
            ['adguard', json.dumps(data)]
        )
        commit(conn)

        # Broadcast update
        from app.core.notifications import manager
        manager.broadcast_sync({
            "type": "integration_status",
            "integration": "adguard",
            "data": { "verified": data["verified"], "error": data.get("error") }
        })

        return {"status": "saved", "verified": data["verified"]}
    except Exception as e:
        logger.error(f"Failed to save Adguard config: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@router.post("/verify")
def verify_connection(config: AdguardConfig):
    try:
        client = AdguardClient(config.url, config.username, config.password)
        client.test_connection()
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Connection failed: {str(e)}")

@router.post("/sync")
def trigger_sync(background_tasks: BackgroundTasks):
    conn = get_connection()
    try:
        row = conn.execute("SELECT config FROM integrations WHERE name = 'adguard'").fetchone()
        if not row:
            raise HTTPException(status_code=400, detail="Adguard not configured")
        
        conf = json.loads(row[0])
        if not conf.get("url"):
             raise HTTPException(status_code=400, detail="Adguard URL missing")
             
        client = AdguardClient(conf["url"], conf.get("username"), conf.get("password"))
        
        background_tasks.add_task(client.sync, force=True)
        return {"status": "queued", "message": "Adguard sync started in background"}
    finally:
        conn.close()

class ProtectionState(BaseModel):
    enabled: bool

@router.post("/protection")
def set_protection_status(state: ProtectionState):
    conn = get_connection()
    try:
        row = conn.execute("SELECT config FROM integrations WHERE name = 'adguard'").fetchone()
        if not row:
            raise HTTPException(status_code=400, detail="Adguard not configured")
        
        conf = json.loads(row[0])
        client = AdguardClient(conf["url"], conf.get("username"), conf.get("password"))
        
        client.set_protection(state.enabled)
        return {"status": "success", "protection_enabled": state.enabled}
    except Exception as e:
        logger.error(f"Failed to toggle Adguard protection: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.get("/data")
def get_adguard_data():
    conn = get_connection()
    try:
        # Check config & verified
        row = conn.execute("SELECT config FROM integrations WHERE name = 'adguard'").fetchone()
        config = json.loads(row[0]) if row else {}

        verified = config.get("verified", False)
        if not verified or not config.get("enabled", True):
            return {
                "verified": verified,
                "enabled": config.get("enabled", False),
                "stats": None
            }

        # Query stats from DNS db
        from app.core.dns_db import get_dns_connection
        from app.core.date_utils import now as utc_now
        from datetime import timedelta
        conn_dns = get_dns_connection()
        
        now = utc_now()
        start_24h = now - timedelta(hours=24)
        
        try:
            # 24h Stats
            stats_row = conn_dns.execute(
                """
                SELECT 
                    COUNT(*), 
                    COUNT(CASE WHEN is_blocked = TRUE THEN 1 END),
                    AVG(response_time)
                FROM dns_logs
                WHERE timestamp >= ?
                """,
                [start_24h]
            ).fetchone()
            
            total = stats_row[0] or 0
            blocked = stats_row[1] or 0
            avg_time = stats_row[2] or 0
            
            # Recent Blocked Queries (Top 10)
            blocked_rows = conn_dns.execute(
                """
                SELECT l.timestamp, d.domain, l.client_ip, l.query_type, d.category
                FROM dns_logs l
                JOIN dns_domains d ON l.domain_id = d.id
                WHERE l.is_blocked = TRUE
                ORDER BY l.timestamp DESC
                LIMIT 100
                """
            ).fetchall()
            
            recent_blocked = [
                {
                    "timestamp": r[0].isoformat() if r[0] else None,
                    "domain": r[1],
                    "client_ip": r[2],
                    "query_type": r[3],
                    "category": r[4]
                }
                for r in blocked_rows
            ]

            # Get protection status
            protection_enabled = False
            try:
                client = AdguardClient(config["url"], config.get("username"), config.get("password"))
                protection_enabled = client.get_protection_status()
            except Exception as e:
                logger.warning(f"Failed to get protection status: {e}")

            return {
                "verified": verified,
                "enabled": config.get("enabled", True),
                "protection_enabled": protection_enabled,
                "last_run": config.get("last_run"),
                "url": config.get("url"),
                "stats": {
                    "total_queries_24h": total,
                    "blocked_queries_24h": blocked,
                    "block_percentage_24h": round((blocked / total * 100), 2) if total > 0 else 0,
                    "avg_response_time_ms": round(avg_time, 2)
                },
                "recent_blocked": recent_blocked
            }
        except Exception as dns_err:
            logger.error(f"Error querying DNS DB for Adguard tab: {dns_err}")
            return {
                "verified": verified,
                "enabled": config.get("enabled", True),
                "last_run": config.get("last_run"),
                "url": config.get("url"),
                "stats": None
            }
    except Exception as e:
        logger.error(f"Error fetching Adguard integration data: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

