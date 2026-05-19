import asyncio
import logging
from typing import Optional
from datetime import datetime, timezone, timedelta
from app.core.date_utils import now as utc_now
from app.core.db import get_connection
from app.services.scans import run_scan_job

logger = logging.getLogger(__name__)


async def enqueue_scan(target: str, scan_type: str) -> Optional[str]:
    from uuid import uuid4
    def sync_enqueue():
        conn = get_connection()
        try:
            t = target.strip()
            now = utc_now()
            
            # Check for exactly same scan (target + type) already queued or running
            active = conn.execute(
                "SELECT id FROM scans WHERE status IN ('queued', 'running') AND target = ? AND scan_type = ?", 
                [t, scan_type]
            ).fetchone()
            
            if active:
                logger.info(f"Scan for {t} ({scan_type}) already in progress. Skipping.")
                return None

            scan_id = str(uuid4())
            conn.execute("INSERT INTO scans (id, target, scan_type, status, created_at) VALUES (?, ?, ?, 'queued', ?)", [scan_id, t, scan_type, now])
            from app.core.db import commit
            commit()
            return scan_id
        finally:
            conn.close()
    return await asyncio.to_thread(sync_enqueue)


async def handle_queued_scans(cleanup=False):
    def get_job():
        conn = get_connection()
        try:
            now = utc_now()
            
            if cleanup:
                # Re-clean stale scans (interrupted)
                stale_cutoff = now - timedelta(minutes=20)
                conn.execute(
                    "UPDATE scans SET status='error', finished_at=?, error_message='Job timed out or interrupted' WHERE status='running' AND started_at < ?", 
                    [now, stale_cutoff]
                )
            
            # One scan at a time for stability on Pi
            row = conn.execute(
                "SELECT id, target, scan_type FROM scans WHERE status = 'queued' ORDER BY created_at ASC LIMIT 1"
            ).fetchone()
            
            if row:
                conn.execute("UPDATE scans SET status='running', started_at=? WHERE id=?", [now, row[0]])
            
            from app.core.db import commit
            commit()
            return row
        finally:
            conn.close()

    job = await asyncio.to_thread(get_job)
    if not job: return
    
    scan_id, target, scan_type = job
    try:
        await run_scan_job(scan_id, target, scan_type)
        # Note: run_scan_job now marks itself as 'done' or 'error' 
    except Exception as e:
        logger.error(f"Unexpected top-level worker error for {scan_id}: {e}")


async def scan_runner_loop():
    last_cleanup = datetime.min.replace(tzinfo=timezone.utc)
    while True:
        try:
            now = utc_now()
            # Only cleanup stale scans every 60 seconds
            run_cleanup = (now - last_cleanup).total_seconds() > 60
            
            job = await handle_queued_scans(cleanup=run_cleanup)
            if run_cleanup:
                last_cleanup = now
                
        except Exception as e:
            logger.error(f"Error in scan_runner_loop: {e}")
            
        # Sleep 2s to reduce idle CPU (responsiveness is still good enough)
        await asyncio.sleep(2)
