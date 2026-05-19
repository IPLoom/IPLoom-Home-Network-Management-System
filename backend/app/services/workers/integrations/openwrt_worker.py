import asyncio
import logging
import json
from datetime import timedelta
from app.core.date_utils import now as utc_now, parse_iso_utc
from app.core.db import get_connection, commit

logger = logging.getLogger(__name__)


def check_openwrt_schedule(conn, now, active_tasks: set) -> tuple[bool, dict]:
    """Check if OpenWRT sync is due. Returns (should_trigger, config_dict)."""
    try:
        if conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='integrations'").fetchone():
            ow_row = conn.execute("SELECT config FROM integrations WHERE name = 'openwrt'").fetchone()
            if ow_row:
                ow_config = json.loads(ow_row[0])
                if ow_config.get("url") and ow_config.get("username"):
                    interval_mins = int(ow_config.get("interval", 15))
                    last_run_str = ow_config.get("last_run") or ow_config.get("last_sync")
                    
                    should_run = False
                    if not last_run_str:
                        should_run = True
                    else:
                        try:
                            last_run = parse_iso_utc(last_run_str)
                            if now >= last_run + timedelta(minutes=interval_mins):
                                should_run = True
                        except:
                            should_run = True
                    
                    if should_run and "openwrt" not in active_tasks:
                        return True, ow_config
    except Exception as e:
        logger.error(f"Error checking OpenWRT schedule: {e}")
    return False, {}


async def run_openwrt_sync(openwrt_conf: dict, active_tasks: set):
    """Execute OpenWRT sync in background."""
    if "openwrt" in active_tasks:
        return
    active_tasks.add("openwrt")
    try:
        from app.services.integrations.openwrt import OpenWRTClient
        logger.info("Starting scheduled OpenWRT sync...")
        client = OpenWRTClient(openwrt_conf["url"], openwrt_conf["username"], openwrt_conf.get("password"))
        await asyncio.to_thread(client.sync)
        
        # Update last_sync data cursor (only on success)
        def update_ts():
            conn = get_connection()
            try:
                row = conn.execute("SELECT config FROM integrations WHERE name = 'openwrt'").fetchone()
                if row:
                    c = json.loads(row[0])
                    c["last_sync"] = utc_now().isoformat()
                    conn.execute("UPDATE integrations SET config = ? WHERE name = 'openwrt'", [json.dumps(c)])
                    commit()
            finally:
                conn.close()
        await asyncio.to_thread(update_ts)
        logger.info("OpenWRT sync completed.")
    except Exception as e:
        logger.error(f"OpenWRT sync failed: {e}")
    finally:
        active_tasks.discard("openwrt")


async def trigger_openwrt(openwrt_conf: dict, active_tasks: set):
    """Spawn OpenWRT sync task and update last_run heartbeat immediately."""
    asyncio.create_task(run_openwrt_sync(openwrt_conf, active_tasks))
    
    # Update last_run heartbeat IMMEDIATELY to prevent fail-spam (retrying every 5s on failure)
    def update_last_run_ow():
        conn = get_connection()
        try:
            row = conn.execute("SELECT config FROM integrations WHERE name = 'openwrt'").fetchone()
            if row:
                c = json.loads(row[0])
                c["last_run"] = utc_now().isoformat()
                conn.execute("UPDATE integrations SET config = ? WHERE name = 'openwrt'", [json.dumps(c)])
                commit()
        finally:
            conn.close()
    await asyncio.to_thread(update_last_run_ow)
