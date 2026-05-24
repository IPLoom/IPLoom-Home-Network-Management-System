import json
import logging
import httpx
import re
import asyncio
from datetime import datetime, timezone, timedelta
from app.core.date_utils import now as utc_now
from uuid import uuid4
from typing import Optional, List, Dict, Any

from app.core.db import get_connection
from app.services.mqtt import publish_device_online, publish_device_offline
from app.core.task_logger import log_task_event

logger = logging.getLogger(__name__)

# Standard columns for device SELECTs
DEVICE_COLUMNS = """
    d.id, d.ip, d.mac, d.name, d.display_name, d.device_type, d.first_seen, d.last_seen, 
    d.vendor, d.icon, d.status, d.ip_type, d.open_ports, d.attributes, d.is_trusted, 
    d.brand, d.brand_icon, d.parent_id, d.is_blocked, d.has_schedule, d.is_manual_block, 
    d.is_scheduled_block, d.is_quota_exceeded, d.is_manual_unblock,
    q.limit_bytes, q.current_usage, q.enabled as quota_enabled
"""

def get_base_query():
    return f"SELECT {DEVICE_COLUMNS} FROM devices d LEFT JOIN device_quotas q ON d.id = q.device_id"

def row_to_dict(row, conn=None):
    if not row: return None
    attributes = json.loads(row[13]) if row[13] and isinstance(row[13], str) else (row[13] if row[13] else {})
    if conn and row[0]:
        try:
            src_rows = conn.execute("SELECT attributes FROM device_discovery_sources WHERE device_id = ? ORDER BY last_seen ASC", [row[0]]).fetchall()
            for s in src_rows:
                if s[0]:
                    try:
                        s_attrs = json.loads(s[0]) if isinstance(s[0], str) else (s[0] if s[0] else {})
                        attributes.update(s_attrs)
                    except Exception as e:
                        pass
        except Exception as e:
            pass
            
    d = {
        "id": row[0],
        "ip": row[1],
        "mac": row[2],
        "name": row[3],
        "display_name": row[4],
        "device_type": row[5],
        "first_seen": row[6],
        "last_seen": row[7],
        "vendor": row[8],
        "icon": row[9],
        "status": row[10],
        "ip_type": row[11],
        "open_ports": json.loads(row[12]) if row[12] and isinstance(row[12], str) else (row[12] if row[12] else []),
        "attributes": attributes,
        "is_trusted": bool(row[14])
    }
    if len(row) > 15: d["brand"] = row[15]
    if len(row) > 16: d["brand_icon"] = row[16]
    if len(row) > 17: d["parent_id"] = row[17]
    if len(row) > 18: d["is_blocked"] = bool(row[18])
    if len(row) > 19: d["has_schedule"] = bool(row[19])
    if len(row) > 20: d["is_manual_block"] = bool(row[20])
    if len(row) > 21: d["is_scheduled_block"] = bool(row[21])
    if len(row) > 22: d["is_quota_exceeded"] = bool(row[22])
    if len(row) > 23: d["is_manual_unblock"] = bool(row[23])
    
    # Quota joined columns
    if len(row) > 24:
        d["quota"] = {
            "limit_bytes": row[24],
            "current_usage": row[25],
            "enabled": bool(row[26])
        } if row[24] is not None else None
        
    return d

async def upsert_device_from_scan(
    ip: str,
    mac: Optional[str],
    hostname: Optional[str],
    ports: List[Dict[str, Any]],
) -> str:
    """Wrapper for backward compatibility, uses batch_upsert for safety."""
    res = await batch_upsert_devices([{"ip": ip, "mac": mac, "hostname": hostname, "ports": ports}])
    return res[0] if res else ""

async def batch_upsert_devices(devices_data: List[Dict[str, Any]]) -> List[str]:
    """
    Upserts multiple devices in a single database transaction.
    Greatly reduces DuckDB 'Database is locked' issues.
    """
    if not devices_data:
        return []

    def _sync_batch_upsert_inner():
        conn = get_connection()
        try:
            now = utc_now()
            upserted_ids = []
            new_devices_to_enrich = [] # (id, mac)
            online_notifications = [] # device_info dicts
            
            new_count = 0
            recovered_count = 0
            last_new_device = None
            last_recovered_device = None

            from app.services.classification import classify_device, get_vendor_locally

            for data in devices_data:
                ip = data["ip"]
                mac = data.get("mac")
                
                # Format and clean MAC: treat "unknown"/empty as None (NULL)
                if mac:
                    mac = format_mac(mac)
                    if not mac or mac.lower() in ("unknown", "n/a", "none"):
                        mac = None
                        
                hostname = data.get("hostname")
                ports = data.get("ports", [])
                
                device_id = None
                existing_device = None
                
                # Optimized: Fetch all necessary fields in one go
                if mac:
                    existing_device = conn.execute(
                        f"{get_base_query()} WHERE d.mac = ?", 
                        [mac]
                    ).fetchone()
                
                if not existing_device:
                    existing_device = conn.execute(
                        f"{get_base_query()} WHERE d.ip = ?", 
                        [ip]
                    ).fetchone()

                is_new = False
                old_status = 'unknown'
                
                port_numbers = [p["port"] for p in ports]
                classification = classify_device(hostname, None, port_numbers, page_title=data.get("page_title"))
                guessed_type = classification["type"]
                guessed_icon = classification["icon"]
                guessed_brand = classification.get("brand")
                guessed_brand_icon = classification.get("brand_icon")

                if existing_device:
                    # Map the row using our standard helper
                    dev = row_to_dict(existing_device, conn)
                    device_id = dev["id"]
                    is_trusted = dev["is_trusted"]
                    old_status = dev["status"]
                    
                    if is_trusted:
                        # Only update telemetry/status for trusted devices
                        conn.execute(
                            "UPDATE devices SET last_seen = ?, ip = ?, mac = COALESCE(?, mac), open_ports = ?, status = 'online', missing_count = 0 WHERE id = ?",
                            [now, ip, mac, json.dumps(ports), device_id]
                        )
                        final_name = dev["display_name"] or dev["name"]
                        final_type = dev["device_type"]
                        final_icon = dev["icon"]
                        final_brand = dev["brand"]
                        final_brand_icon = dev["brand_icon"]
                    else:
                        # Update metadata for non-trusted devices if we have better info
                        final_icon = dev["icon"] if (dev["icon"] and dev["icon"] != 'help-circle') else guessed_icon
                        final_type = dev["device_type"] if (dev["device_type"] and dev["device_type"] != 'unknown') else guessed_type
                        final_brand = dev["brand"] if dev["brand"] else guessed_brand
                        final_brand_icon = dev["brand_icon"] if dev["brand_icon"] else guessed_brand_icon
                        final_name = dev["name"] if dev["name"] else hostname
                        
                        conn.execute(
                            """
                            UPDATE devices
                            SET last_seen = ?,
                                ip = ?,
                                mac = COALESCE(?, mac),
                                name = ?,
                                device_type = ?,
                                icon = ?,
                                brand = ?,
                                brand_icon = ?,
                                open_ports = ?,
                                status = ?,
                                missing_count = 0
                            WHERE id = ?
                            """,
                            [now, ip, mac, final_name, final_type, final_icon, final_brand, final_brand_icon, json.dumps(ports), 'online', device_id]
                        )
                else:
                    is_new = True
                    device_id = str(uuid4())
                    conn.execute(
                        """
                        INSERT INTO devices (id, ip, mac, name, display_name, device_type, icon, brand, brand_icon, ip_type, open_ports, first_seen, last_seen, attributes, status, missing_count)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'online', 0)
                        """,
                        [device_id, ip, mac, hostname, hostname or ip, guessed_type, guessed_icon, guessed_brand, guessed_brand_icon, data.get("ip_type"), json.dumps(ports), now, now, "{}"]
                    )

                # Record status change if needed
                if old_status != 'online':
                    conn.execute(
                        "INSERT INTO device_status_history (id, device_id, status, changed_at) VALUES (?, ?, ?, ?)",
                        [str(uuid4()), device_id, 'online', now]
                    )

                for p in ports:
                    p_proto = p.get("protocol", "tcp").lower()
                    conn.execute(
                        """
                        INSERT OR REPLACE INTO device_ports (device_id, port, protocol, service, last_seen)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        [device_id, p["port"], p_proto, p["service"], now]
                    )

                all_ports_rows = conn.execute(
                    "SELECT port, protocol, service FROM device_ports WHERE device_id = ? ORDER BY port",
                    [device_id]
                ).fetchall()
                all_ports = [{"port": r[0], "protocol": r[1], "service": r[2]} for r in all_ports_rows]

                conn.execute(
                    "UPDATE devices SET open_ports = ?, last_seen = ?, status = 'online', missing_count = 0 WHERE id = ?",
                    [json.dumps(all_ports), now, device_id]
                )

                if mac:
                    local_vendor = get_vendor_locally(mac)
                    if local_vendor:
                        conn.execute("UPDATE devices SET vendor = COALESCE(vendor, ?) WHERE id = ?", [local_vendor, device_id])
                
                # Update discovery sources and recalculate status
                conn.execute(
                    """
                    INSERT OR REPLACE INTO device_discovery_sources (device_id, source, last_seen, status, attributes)
                    VALUES (?, 'ping_scan', ?, 'online', ?)
                    """,
                    [device_id, now, json.dumps({"ip": ip, "hostname": hostname or ""})]
                )
                recalculate_device_status(conn, device_id)
                
                upserted_ids.append(device_id)
                if mac:
                    new_devices_to_enrich.append((device_id, mac))
                
                # Collect stats for batched notifications
                if is_new:
                    new_count += 1
                    last_new_device = {"ip": ip, "name": hostname or ip, "id": device_id}
                elif old_status != 'online':
                    recovered_count += 1
                    last_recovered_device = {"ip": ip, "name": hostname or ip, "id": device_id}

                # Always notify on discovery to ensure MQTT state (HA) stays fresh
                dev_row = conn.execute(f"{get_base_query()} WHERE d.id = ?", [device_id]).fetchone()
                if dev_row:
                    dev_data = row_to_dict(dev_row, conn)
                    online_notifications.append({
                        "ip": dev_data["ip"], 
                        "mac": dev_data["mac"], 
                        "hostname": dev_data["display_name"] or dev_data["name"], 
                        "vendor": dev_data["vendor"], 
                        "icon": dev_data["icon"], 
                        "device_type": dev_data["device_type"],
                        "ip_type": dev_data["ip_type"], 
                        "last_seen": dev_data["last_seen"],
                        "brand": dev_data.get("brand"), 
                        "brand_icon": dev_data.get("brand_icon")
                    })

            # Send batched notifications after processing all devices
            if new_count == 1:
                log_task_event("discovery", "new_device", f"New device discovered: {last_new_device['name']}", target=last_new_device['id'], details={"ip": last_new_device['ip']})
            else:
                log_task_event("discovery", "new_device", f"Discovered {new_count} new devices", details={"count": new_count})
        
            if recovered_count > 0:
                if recovered_count == 1:
                    log_task_event("discovery", "status_changed", f"Device is back online: {last_recovered_device['name']}", target=last_recovered_device['id'], details={"ip": last_recovered_device['ip'], "status": "online"})
                else:
                    log_task_event("discovery", "status_changed", f"{recovered_count} devices came back online", details={"count": recovered_count, "status": "online"})

            from app.core.db import commit
            commit()
            return upserted_ids, new_devices_to_enrich, online_notifications
        finally:
            conn.close()

    def sync_batch_upsert():
        import time
        max_retries = 3
        for attempt in range(max_retries):
            try:
                return _sync_batch_upsert_inner()
            except Exception as e:
                err_str = str(e).lower()
                if "write-write conflict" in err_str or "database is locked" in err_str:
                    if attempt < max_retries - 1:
                        logger.warning(f"Database lock or write conflict (attempt {attempt+1}/{max_retries}). Retrying in 1s...")
                        time.sleep(1)
                    else:
                        logger.error(f"Failed to batch upsert devices after {max_retries} attempts: {e}")
                        raise
                else:
                    raise

    upserted_ids, to_enrich, to_notify = await asyncio.to_thread(sync_batch_upsert)

    # Trigger MQTT notifications
    for dev_info in to_notify:
        await asyncio.to_thread(publish_device_online, dev_info)

    # Background enrichment for each found device (async)
    for d_id, mac in to_enrich:
        asyncio.create_task(enrich_device(d_id, mac))
        
    return upserted_ids


async def record_status_change(conn, device_id: str, status: str, timestamp: datetime):
    # This remains for internal use if a connection is already open
    if not conn:
        def sync_record():
            c = get_connection()
            try:
                c.execute(
                    "INSERT INTO device_status_history (id, device_id, status, changed_at) VALUES (?, ?, ?, ?)",
                    [str(uuid4()), device_id, status, timestamp]
                )
                from app.core.db import commit
                commit()
            finally:
                c.close()
        await asyncio.to_thread(sync_record)
    else:
        conn.execute(
            "INSERT INTO device_status_history (id, device_id, status, changed_at) VALUES (?, ?, ?, ?)",
            [str(uuid4()), device_id, status, timestamp]
        )

def format_mac(mac: str) -> str:
    if not mac or mac.lower() == "unknown": return ""
    clean = "".join(c for c in mac if c.isalnum()).upper()
    if len(clean) != 12 or not all(c in "0123456789ABCDEF" for c in clean):
        return "" 
    return ":".join(clean[i:i+2] for i in range(0, 12, 2))



async def enrich_device(device_id: str, mac: str):
    from app.services.classification import get_vendor_locally, classify_device
    import re
    
    mac = format_mac(mac)
    if not mac: return

    def get_device_details():
        conn = get_connection()
        try:
            row = conn.execute("SELECT vendor, is_trusted FROM devices WHERE id = ?", [device_id]).fetchone()
            if row:
                return row[0], bool(row[1])
            return None, False
        finally:
            conn.close()
            
    existing_vendor, is_trusted = await asyncio.to_thread(get_device_details)
    
    # If device is trusted, stop enrichment from touching it during auto-scans
    if is_trusted:
        logger.debug(f"Skipping enrichment for trusted device {device_id}")
        return

    # Check if we already have a vendor
    has_vendor = existing_vendor and existing_vendor.lower() != "unknown" and existing_vendor.strip() != ""
    
    vendor = None
    if has_vendor:
        vendor = existing_vendor
    else:
        # Check if another device with same MAC already has a vendor
        def get_vendor_by_mac():
            conn = get_connection()
            try:
                row = conn.execute("SELECT vendor FROM devices WHERE mac = ? AND vendor IS NOT NULL AND vendor != 'unknown' AND vendor != '' LIMIT 1", [mac]).fetchone()
                return row[0] if row else None
            finally:
                conn.close()
        mac_vendor = await asyncio.to_thread(get_vendor_by_mac)
        if mac_vendor:
            vendor = mac_vendor
        else:
            vendor = get_vendor_locally(mac)
            
    # Fetch from API only if we don't have a vendor
    if not vendor:
        from app.utilities.mac_lookup import get_vendor_from_api
        vendor = await get_vendor_from_api(mac)

    def get_ip():
        conn = get_connection()
        try:
            row = conn.execute("SELECT ip FROM devices WHERE id = ?", [device_id]).fetchone()
            return row[0] if row else None
        finally:
            conn.close()
    
    ip = await asyncio.to_thread(get_ip)
    if not ip: return

    if vendor:
        from app.services.fingerprinting import FingerprintService
        fingerprint = await FingerprintService.fingerprint_device(ip)

        def sync_update():
            conn = get_connection()
            try:
                row = conn.execute(f"{get_base_query()} WHERE d.id = ?", [device_id]).fetchone()
                if row:
                    dev = row_to_dict(row, conn)
                    display_name = dev["display_name"]
                    current_type = dev["device_type"]
                    current_icon = dev["icon"]
                    attrs = dev["attributes"]
                    current_brand = dev.get("brand")
                    current_brand_icon = dev.get("brand_icon")
                    is_trusted = dev["is_trusted"]
                    
                    # Double check trusted
                    if is_trusted:
                        return

                    # Never overwrite user-customized details
                    icon_is_user_set = current_icon and current_icon != 'help-circle'
                    type_is_user_set = current_type and current_type != 'unknown'
                    brand_is_user_set = current_brand is not None
                    name_is_user_set = display_name and not re.match(r"^\d+\.\d+\.\d+\.\d+$", display_name)

                    new_type, new_icon = current_type, current_icon
                    new_brand, new_brand_icon = current_brand, current_brand_icon
                    new_display = display_name
                    
                    attrs = dev["attributes"]
                    attrs["vendor"] = vendor
                    
                    # Enhanced classification using current info
                    classification = classify_device(
                        hostname=display_name, 
                        vendor=vendor, 
                        ports=[], 
                        page_title=attrs.get("web_title")
                    )
                    
                    if fingerprint:
                        # Fingerprint is a high-confidence match — always override
                        new_type = fingerprint["type"]
                        new_icon = fingerprint["icon"]
                        if not name_is_user_set:
                            new_display = fingerprint["name"]
                        attrs["fingerprint_id"] = fingerprint["id"]
                        attrs["web_interface"] = fingerprint["url"]
                        if fingerprint.get("detected_title"):
                            attrs["web_title"] = fingerprint["detected_title"]
                        if fingerprint.get("brand"):
                            new_brand = fingerprint["brand"].capitalize()
                            from app.services.classification import get_custom_assets
                            assets = get_custom_assets()
                            brand_asset = assets.get(fingerprint["brand"].lower())
                            new_brand_icon = brand_asset["path"] if brand_asset else None
                    else:
                        if not type_is_user_set:
                            new_type = classification["type"]
                        if not icon_is_user_set:
                            new_icon = classification["icon"]
                        if not brand_is_user_set:
                            new_brand = classification.get("brand")
                            new_brand_icon = classification.get("brand_icon")
                        
                        if not name_is_user_set:
                            new_display = vendor
                    conn.execute(
                        "UPDATE devices SET vendor = COALESCE(vendor, ?), device_type = ?, icon = ?, brand = ?, brand_icon = ?, display_name = ?, attributes = ? WHERE id = ?",
                        [vendor, new_type, new_icon, new_brand, new_brand_icon, new_display, json.dumps(attrs), device_id]
                    )
                from app.core.db import commit
                commit()
            finally:
                conn.close()
        await asyncio.to_thread(sync_update)
        
        def sync_notify():
            conn = get_connection()
            try:
                row = conn.execute(f"{get_base_query()} WHERE d.id = ?", [device_id]).fetchone()
                if row:
                    dev = row_to_dict(row, conn)
                    publish_device_online({
                        "ip": dev["ip"], 
                        "mac": dev["mac"], 
                        "hostname": dev["display_name"] or dev["name"], 
                        "vendor": dev["vendor"], 
                        "icon": dev["icon"], 
                        "device_type": dev["device_type"],
                        "ip_type": dev["ip_type"], 
                        "last_seen": dev["last_seen"],
                        "brand": dev.get("brand"), 
                        "brand_icon": dev.get("brand_icon")
                    })
            finally:
                conn.close()
        await asyncio.to_thread(sync_notify)

async def update_device_fields(device_id: str, fields: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    # Get current device info to check for ip_type changes
    def get_current_info():
        conn = get_connection()
        try:
            row = conn.execute(f"{get_base_query()} WHERE d.id = ?", [device_id]).fetchone()
            return row_to_dict(row, conn) if row else None
        finally:
            conn.close()
            
    old_dev = await asyncio.to_thread(get_current_info)

    # Check if we need to call OpenWrt for IP reservation BEFORE updating the database
    wrt_action = None
    mac = old_dev.get("mac") if old_dev else None
    ip = old_dev.get("ip") if old_dev else None
    
    # Use the requested hostname if available, otherwise fallback to existing
    req_display = fields.get("display_name")
    req_name = fields.get("name")
    hostname = req_display or req_name or (old_dev.get("display_name") or old_dev.get("name")) if old_dev else None

    if old_dev and mac and ip and "ip_type" in fields:
        old_ip_type = old_dev.get("ip_type") or "dynamic"
        new_ip_type = fields["ip_type"]
        if old_ip_type != new_ip_type:
            if new_ip_type == "static":
                wrt_action = "reserve"
            elif new_ip_type == "dynamic":
                wrt_action = "unreserve"

    if wrt_action:
        # Check if OpenWrt is verified and enabled
        def check_openwrt_config():
            conn = get_connection()
            try:
                row = conn.execute("SELECT config FROM integrations WHERE name = 'openwrt'").fetchone()
                v_row = conn.execute("SELECT value FROM config WHERE key = 'openwrt_verified'").fetchone()
                is_verified = (v_row[0] == "true") if v_row else False
                return json.loads(row[0]) if row else None, is_verified
            finally:
                conn.close()
        
        openwrt_config, is_verified = await asyncio.to_thread(check_openwrt_config)
        if openwrt_config and openwrt_config.get("enabled", True) and is_verified:
            try:
                from app.services.integrations.openwrt import OpenWRTClient
                client = OpenWRTClient(openwrt_config["url"], openwrt_config["username"], openwrt_config.get("password"))
                if wrt_action == "reserve":
                    await asyncio.to_thread(client.reserve_ip, mac, ip, hostname)
                elif wrt_action == "unreserve":
                    await asyncio.to_thread(client.unreserve_ip, mac)
            except Exception as e:
                logger.error(f"Failed to {wrt_action} IP on OpenWrt: {e}")
                # Raise immediately so the local database is not updated
                raise RuntimeError(str(e))

    def sync_update():
        conn = get_connection()
        try:
            row = conn.execute(f"{get_base_query()} WHERE d.id = ?", [device_id]).fetchone()
            if not row: return None
            valid_cols = {
                'name', 'display_name', 'device_type', 'icon', 'attributes', 
                'ip_type', 'is_trusted', 'parent_id', 'brand', 'brand_icon', 
                'vendor', 'open_ports', 'is_manual_block', 'is_manual_unblock'
            }
            updates = []
            params = []
            trigger_policy = False
            for k, v in fields.items():
                if k in valid_cols:
                    if k in ('is_manual_block', 'is_manual_unblock'):
                        trigger_policy = True
                    # Handle JSON serialization for dict/list fields
                    if k in ('attributes', 'open_ports') and not isinstance(v, str):
                        v = json.dumps(v)
                    updates.append(f"{k} = ?")
                    params.append(v)
            if updates:
                params.append(device_id)
                conn.execute(f"UPDATE devices SET {', '.join(updates)} WHERE id = ?", params)
                from app.core.db import commit
                commit()
            updated = conn.execute(f"{get_base_query()} WHERE d.id = ?", [device_id]).fetchone()
            return row_to_dict(updated, conn)
        finally:
            conn.close()

    dev_info = await asyncio.to_thread(sync_update)
    if not dev_info: return None

    # Trigger policy re-evaluation if manual override flags were changed
    if any(k in fields for k in ('is_manual_block', 'is_manual_unblock')):
        from app.services.policy import apply_device_policy
        await apply_device_policy(device_id)
    
    # Notify MQTT about the update
    await asyncio.to_thread(publish_device_online, {
        "ip": dev_info["ip"], 
        "mac": dev_info["mac"], 
        "hostname": dev_info["display_name"] or dev_info["name"],
        "vendor": dev_info["vendor"], 
        "icon": dev_info["icon"], 
        "device_type": dev_info["device_type"],
        "ip_type": dev_info["ip_type"], 
        "last_seen": dev_info["last_seen"],
        "brand": dev_info.get("brand"), 
        "brand_icon": dev_info.get("brand_icon")
    })
    return dev_info


def recalculate_device_status(conn, device_id: str):
    """
    Recalculates a device's overall status and last_seen based on its active discovery sources.
    Overall last_seen: The maximum last_seen among all sources.
    Overall status: 'online' if any source has status = 'online' and last_seen is within the TTL window.
      TTL thresholds:
      - ping_scan, arp: 15 minutes (since ping scans are rapid but devices can disconnect)
      - openwrt, deco, adguard: 45 minutes (since DHCP leases / sync intervals might be longer)
    If all sources are offline or exceed their TTLs, the overall status is set to 'offline'.
    """
    sources = conn.execute(
        "SELECT source, status, last_seen FROM device_discovery_sources WHERE device_id = ?",
        [device_id]
    ).fetchall()
    
    if not sources:
        return
        
    overall_status = "offline"
    max_last_seen = None
    
    from app.core.date_utils import now as utc_now, parse_iso_utc
    now = utc_now().replace(tzinfo=None)
    
    for src, status, last_seen in sources:
        if not last_seen:
            continue
            
        if isinstance(last_seen, str):
            try:
                dt = parse_iso_utc(last_seen).replace(tzinfo=None)
            except:
                dt = now
        else:
            dt = last_seen
            if dt.tzinfo is not None:
                dt = dt.replace(tzinfo=None)
            
        if max_last_seen is None or dt > max_last_seen:
            max_last_seen = dt
            
        ttl_minutes = 45 if src in ('openwrt', 'deco', 'adguard') else 15
        is_fresh = (now - dt) < timedelta(minutes=ttl_minutes)
        
        if status == 'online' and is_fresh:
            overall_status = "online"

    old_row = conn.execute("SELECT status, last_seen FROM devices WHERE id = ?", [device_id]).fetchone()
    old_status = old_row[0] if old_row else "unknown"
    
    final_last_seen = max_last_seen or now
    
    missing_count_update = "missing_count = 0" if overall_status == 'online' else "missing_count = missing_count"
    
    conn.execute(
        f"UPDATE devices SET status = ?, last_seen = ?, {missing_count_update} WHERE id = ?",
        [overall_status, final_last_seen, device_id]
    )
    
    if old_status != overall_status:
        conn.execute(
            "INSERT INTO device_status_history (id, device_id, status, changed_at) VALUES (?, ?, ?, ?)",
            [str(uuid4()), device_id, overall_status, now]
        )

