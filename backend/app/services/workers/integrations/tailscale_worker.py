import asyncio
import logging
import json
from datetime import timedelta
from app.core.date_utils import now as utc_now, parse_iso_utc
from app.core.db import get_connection, commit

logger = logging.getLogger(__name__)


def check_tailscale_schedule(conn, now, active_tasks: set) -> tuple[bool, dict]:
    """Check if Tailscale sync is due. Returns (should_trigger, config_dict)."""
    try:
        if conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='integrations'").fetchone():
            row = conn.execute("SELECT config FROM integrations WHERE name = 'tailscale'").fetchone()
            if row:
                config = json.loads(row[0])
                if config.get("api_key") and config.get("enabled", True):
                    interval_mins = int(config.get("interval", 15))
                    last_run_str = config.get("last_run") or config.get("last_sync")
                    
                    should_run = False
                    if not last_run_str:
                        logger.info("Tailscale sync never run before. Triggering.")
                        should_run = True
                    else:
                        try:
                            last_run = parse_iso_utc(last_run_str)
                            diff = (now - last_run).total_seconds()
                            target_diff = interval_mins * 60
                            
                            if diff >= target_diff:
                                logger.info(f"Tailscale interval reached: {diff:.1f}s since last run, interval: {target_diff}s. Triggering.")
                                should_run = True
                        except Exception as te:
                            logger.error(f"Error parsing Tailscale last_run '{last_run_str}': {te}")
                            should_run = True
                    
                    if should_run and "tailscale" not in active_tasks:
                        return True, config
    except Exception as e:
        logger.error(f"Error checking Tailscale schedule: {e}")
    return False, {}


async def run_tailscale_sync(tailscale_conf: dict, active_tasks: set):
    """Execute Tailscale sync in background."""
    if "tailscale" in active_tasks:
        return
    active_tasks.add("tailscale")
    try:
        from app.services.integrations.tailscale import TailscaleClient
        logger.info("Starting scheduled Tailscale sync...")
        client = TailscaleClient(tailscale_conf["api_key"], tailscale_conf.get("tailnet", "-"))
        await asyncio.to_thread(client.sync)
        
        # Update last_sync data cursor (only on success)
        def update_ts():
            conn = get_connection()
            try:
                row = conn.execute("SELECT config FROM integrations WHERE name = 'tailscale'").fetchone()
                if row:
                    c = json.loads(row[0])
                    c["last_sync"] = utc_now().isoformat()
                    conn.execute("UPDATE integrations SET config = ? WHERE name = 'tailscale'", [json.dumps(c)])
                    commit()
            finally:
                conn.close()
        await asyncio.to_thread(update_ts)
        logger.info("Tailscale sync completed.")
    except Exception as e:
        logger.error(f"Tailscale sync failed: {e}")
    finally:
        active_tasks.discard("tailscale")


async def trigger_tailscale(tailscale_conf: dict, active_tasks: set):
    """Spawn Tailscale sync task and update last_run heartbeat immediately."""
    asyncio.create_task(run_tailscale_sync(tailscale_conf, active_tasks))

    # Update last_run heartbeat IMMEDIATELY to prevent fail-spam
    def update_last_run():
        conn = get_connection()
        try:
            row = conn.execute("SELECT config FROM integrations WHERE name = 'tailscale'").fetchone()
            if row:
                c = json.loads(row[0])
                c["last_run"] = utc_now().isoformat()
                conn.execute("UPDATE integrations SET config = ? WHERE name = 'tailscale'", [json.dumps(c)])
                commit()
        finally:
            conn.close()
    await asyncio.to_thread(update_last_run)
