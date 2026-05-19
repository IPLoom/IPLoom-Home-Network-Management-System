import asyncio
import logging
import json
from datetime import timedelta
from app.core.date_utils import now as utc_now, parse_iso_utc
from app.core.db import get_connection, commit

logger = logging.getLogger(__name__)


def check_deco_schedule(conn, now, active_tasks: set) -> tuple[bool, dict]:
    """Check if TP-Link Deco sync is due. Returns (should_trigger, config_dict)."""
    try:
        if conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='integrations'").fetchone():
            row = conn.execute("SELECT config FROM integrations WHERE name = 'deco'").fetchone()
            if row:
                config = json.loads(row[0])
                if config.get("host") and config.get("password") and config.get("enabled", True):
                    interval_mins = int(config.get("interval", 15))
                    last_run_str = config.get("last_run") or config.get("last_sync")
                    
                    should_run = False
                    if not last_run_str:
                        logger.info("Deco sync never run before. Triggering.")
                        should_run = True
                    else:
                        try:
                            last_run = parse_iso_utc(last_run_str)
                            diff = (now - last_run).total_seconds()
                            target_diff = interval_mins * 60
                            
                            if diff >= target_diff:
                                logger.info(f"Deco interval reached: {diff:.1f}s since last run, interval: {target_diff}s. Triggering.")
                                should_run = True
                        except Exception as te:
                            logger.error(f"Error parsing Deco last_run '{last_run_str}': {te}")
                            should_run = True
                    
                    if should_run and "deco" not in active_tasks:
                        return True, config
    except Exception as e:
        logger.error(f"Error checking Deco schedule: {e}")
    return False, {}


async def run_deco_sync(deco_conf: dict, active_tasks: set):
    """Execute TP-Link Deco sync in background."""
    if "deco" in active_tasks:
        return
    active_tasks.add("deco")
    try:
        from app.services.integrations.deco import DecoClient
        logger.info("Starting scheduled Deco sync...")
        client = DecoClient(deco_conf["host"], deco_conf["password"])
        await asyncio.to_thread(client.sync)
        
        # Update last_sync data cursor (only on success)
        def update_ts():
            conn = get_connection()
            try:
                row = conn.execute("SELECT config FROM integrations WHERE name = 'deco'").fetchone()
                if row:
                    c = json.loads(row[0])
                    c["last_sync"] = utc_now().isoformat()
                    conn.execute("UPDATE integrations SET config = ? WHERE name = 'deco'", [json.dumps(c)])
                    commit()
            finally:
                conn.close()
        await asyncio.to_thread(update_ts)
        logger.info("Deco sync completed.")
    except Exception as e:
        logger.error(f"Deco sync failed: {e}")
    finally:
        active_tasks.discard("deco")


async def trigger_deco(deco_conf: dict, active_tasks: set):
    """Spawn Deco sync task and update last_run heartbeat immediately."""
    asyncio.create_task(run_deco_sync(deco_conf, active_tasks))

    # Update last_run heartbeat IMMEDIATELY to prevent fail-spam
    def update_last_run():
        conn = get_connection()
        try:
            row = conn.execute("SELECT config FROM integrations WHERE name = 'deco'").fetchone()
            if row:
                c = json.loads(row[0])
                c["last_run"] = utc_now().isoformat()
                conn.execute("UPDATE integrations SET config = ? WHERE name = 'deco'", [json.dumps(c)])
                commit()
        finally:
            conn.close()
    await asyncio.to_thread(update_last_run)
