import asyncio
import logging
import json
from datetime import timedelta
from app.core.date_utils import now as utc_now, parse_iso_utc
from app.core.db import get_connection, commit

logger = logging.getLogger(__name__)


def check_adguard_schedule(conn, now, active_tasks: set) -> tuple[bool, dict]:
    """Check if AdGuard sync is due. Returns (should_trigger, config_dict)."""
    try:
        if conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='integrations'").fetchone():
            ag_row = conn.execute("SELECT config FROM integrations WHERE name = 'adguard'").fetchone()
            if ag_row:
                ag_config = json.loads(ag_row[0])
                if ag_config.get("url") and ag_config.get("username"):
                    interval_mins = int(ag_config.get("interval", 15))
                    last_run_str = ag_config.get("last_run") or ag_config.get("last_sync")
                    
                    should_run = False
                    if not last_run_str:
                        logger.info("AdGuard sync never run before. Triggering.")
                        should_run = True
                    else:
                        try:
                            last_run = parse_iso_utc(last_run_str)
                            diff = (now - last_run).total_seconds()
                            target_diff = interval_mins * 60
                            
                            if diff >= target_diff:
                                logger.info(f"AdGuard interval reached: {diff:.1f}s since last run, interval: {target_diff}s. Triggering.")
                                should_run = True
                        except Exception as te:
                            logger.error(f"Error parsing AdGuard last_run '{last_run_str}': {te}")
                            should_run = True
                    
                    if should_run and "adguard" not in active_tasks:
                        return True, ag_config
    except Exception as e:
        logger.error(f"Error checking AdGuard schedule: {e}")
    return False, {}


async def run_adguard_sync(adguard_conf: dict, active_tasks: set):
    """Execute AdGuard sync in background."""
    if "adguard" in active_tasks:
        return
    active_tasks.add("adguard")
    try:
        from app.services.integrations.adguard import AdguardClient
        logger.info("Starting scheduled AdGuard sync...")
        client = AdguardClient(adguard_conf["url"], adguard_conf["username"], adguard_conf.get("password"))
        await asyncio.to_thread(client.sync)
        
        # Note: last_run for heartbeat is updated immediately after trigger.
        # last_sync (data cursor) is updated inside client.sync itself.
        logger.info("AdGuard sync completed.")
    except Exception as e:
        logger.error(f"AdGuard sync failed: {e}")
    finally:
        active_tasks.discard("adguard")


async def trigger_adguard(adguard_conf: dict, active_tasks: set):
    """Spawn AdGuard sync task and update last_run heartbeat immediately."""
    asyncio.create_task(run_adguard_sync(adguard_conf, active_tasks))

    # Update last_run heartbeat IMMEDIATELY to prevent fail-spam (retrying every 5s on failure)
    def update_last_run_ag():
        conn = get_connection()
        try:
            row = conn.execute("SELECT config FROM integrations WHERE name = 'adguard'").fetchone()
            if row:
                c = json.loads(row[0])
                c["last_run"] = utc_now().isoformat()
                conn.execute("UPDATE integrations SET config = ? WHERE name = 'adguard'", [json.dumps(c)])
                commit()
        finally:
            conn.close()
    await asyncio.to_thread(update_last_run_ag)
