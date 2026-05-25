import asyncio
import logging
import json
from datetime import datetime, timezone, timedelta
from app.core.date_utils import now as utc_now
from app.core.db import get_connection, commit
from app.services.workers.scan_runner import enqueue_scan
from app.services.workers.integrations.openwrt_worker import check_openwrt_schedule, trigger_openwrt
from app.services.workers.integrations.adguard_worker import check_adguard_schedule, trigger_adguard
from app.services.workers.integrations.deco_worker import check_deco_schedule, trigger_deco
from app.services.workers.integrations.tailscale_worker import check_tailscale_schedule, trigger_tailscale
import time

logger = logging.getLogger(__name__)
POLL_INTERVAL_SECONDS = 5

# Concurrency guard for background tasks (shared across all workers)
active_tasks = set()


async def scheduler_loop():
    from app.services.mqtt import MQTTManager
    from app.services.internet_schedules import check_and_apply_schedules
    from app.services.internet_quotas import check_and_apply_quotas
    from app.services.policy import apply_device_policy
    
    last_convergence = 0
    while True:
        try:
            # 1. Handle background scan schedules & Integrations
            await handle_schedules()
            
            # 2. Handle Internet Access Schedules
            await check_and_apply_schedules()
            
            # 3. Handle Internet Data Quotas
            await check_and_apply_quotas()
            
            # 4. Periodically ensure policy convergence (every 60s)
            # This retries any failed router calls from transient errors
            if time.time() - last_convergence > 60:
                last_convergence = time.time()
                try:
                    conn = get_connection()
                    try:
                        # Find devices where DB 'is_blocked' might mismatch combined flags
                        # apply_device_policy has internal check 'if target != current'
                        dev_rows = conn.execute("SELECT id FROM devices").fetchall()
                        for (dev_id,) in dev_rows:
                            await apply_device_policy(dev_id, conn)
                    finally:
                        conn.close()
                except Exception as e:
                    logger.error(f"Error in policy convergence task: {e}")

            # 5. Check MQTT Health
            MQTTManager.get_instance().check_health()
            
        except Exception as e:
            logger.error(f"Error in scheduler_loop: {e}")
        await asyncio.sleep(POLL_INTERVAL_SECONDS)


async def handle_schedules():
    def sync_check():
        conn = get_connection()
        try:
            now = utc_now()
            
            # 1. Fetch Config for Global Discovery
            config_rows = conn.execute("SELECT key, value FROM config WHERE key IN ('scan_subnets', 'scan_interval', 'last_discovery_run_at')").fetchall()
            config = {r[0]: r[1] for r in config_rows}
            
            scan_subnets_raw = config.get('scan_subnets')
            scan_interval = int(config.get('scan_interval', '300'))
            last_run_str = config.get('last_discovery_run_at')
            
            last_run = None
            if last_run_str:
                try:
                    last_run = datetime.fromisoformat(last_run_str.replace('Z', '+00:00'))
                    if last_run.tzinfo is None: last_run = last_run.replace(tzinfo=timezone.utc)
                except: pass
                
            trigger_global = False
            target_for_global = None
            if scan_subnets_raw:
                try:
                    subnets = json.loads(scan_subnets_raw)
                    if isinstance(subnets, list) and subnets:
                        target_for_global = " ".join(sorted([s.strip() for s in subnets if s.strip()]))
                except:
                    target_for_global = scan_subnets_raw.strip()

            if target_for_global:
                if last_run is None:
                    logger.info("No last run record found for global discovery. Triggering now.")
                    trigger_global = True
                elif now >= last_run + timedelta(seconds=scan_interval):
                    diff = (now - last_run).total_seconds()
                    logger.info(f"Global discovery interval reached ({diff}s since last run, interval: {scan_interval}s). Triggering.")
                    trigger_global = True
                else:
                    pass
            elif scan_subnets_raw:
                 # Subnets are empty or invalid, don't spam.
                 pass

            # 2. Handle specific schedules
            rows = conn.execute(
                """
                SELECT id, scan_type, target, interval_seconds
                FROM scan_schedules
                WHERE enabled = TRUE AND (next_run_at IS NULL OR next_run_at <= ?)
                """,
                [now],
            ).fetchall()
            
            # 3. Check integration schedules
            do_openwrt, openwrt_conf = check_openwrt_schedule(conn, now, active_tasks)
            do_adguard, adguard_conf = check_adguard_schedule(conn, now, active_tasks)
            do_deco, deco_conf = check_deco_schedule(conn, now, active_tasks)
            do_tailscale, tailscale_conf = check_tailscale_schedule(conn, now, active_tasks)

            return trigger_global, target_for_global, rows, now, do_openwrt, openwrt_conf, do_adguard, adguard_conf, do_deco, deco_conf, do_tailscale, tailscale_conf
        finally:
            conn.close()

    (trigger_global, target_for_global, schedule_rows, now,
     do_openwrt, openwrt_conf, do_adguard, adguard_conf,
     do_deco, deco_conf, do_tailscale, tailscale_conf) = await asyncio.to_thread(sync_check)

    if trigger_global and target_for_global:
        # Update the timestamp regardless of enqueue success to prevent retry loop.
        await enqueue_scan(target_for_global, "arp")
        
        def update_last_run():
            conn = get_connection()
            try:
                conn.execute("INSERT OR REPLACE INTO config (key, value, updated_at) VALUES ('last_discovery_run_at', ?, ?)", [now.isoformat(), now])
                commit()
                logger.info("Global discovery timestamp updated in DB.")
            except Exception as e:
                logger.error(f"Failed to update global discovery timestamp: {e}")
            finally: conn.close()
        await asyncio.to_thread(update_last_run)

    for sched_id, scan_type, target, interval in schedule_rows:
        enqueued = await enqueue_scan(target, scan_type)
        if enqueued:
            def update_sched():
                conn = get_connection()
                try:
                    next_run_at = now + timedelta(seconds=interval)
                    conn.execute("UPDATE scan_schedules SET last_run_at = ?, next_run_at = ? WHERE id = ?", [now, next_run_at, sched_id])
                    commit()
                finally: conn.close()
            await asyncio.to_thread(update_sched)

    # Trigger integration syncs
    if do_openwrt:
        await trigger_openwrt(openwrt_conf, active_tasks)

    if do_adguard:
        await trigger_adguard(adguard_conf, active_tasks)

    if do_deco:
        await trigger_deco(deco_conf, active_tasks)

    if do_tailscale:
        await trigger_tailscale(tailscale_conf, active_tasks)
