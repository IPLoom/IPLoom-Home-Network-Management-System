import logging
import json
import time
import httpx
from datetime import datetime, timedelta
from app.core.db import get_connection
from app.core.date_utils import now as utc_now
from app.core.task_logger import log_task_event
from app.services.devices import recalculate_device_status
import uuid

logger = logging.getLogger(__name__)

class TailscaleClient:
    def __init__(self, api_key: str, tailnet: str):
        self.api_key = api_key
        self.tailnet = tailnet or "-"
        self.base_url = "https://api.tailscale.com/api/v2"
        # Use IPv4 explicitly to prevent httpx from hanging on broken IPv6 routes
        self.client = httpx.Client(
            auth=(self.api_key, ""),
            transport=httpx.HTTPTransport(local_address="0.0.0.0"),
            timeout=15.0
        )

    def verify(self) -> bool:
        """Verify API credentials by fetching devices."""
        resp = self.client.get(f"{self.base_url}/tailnet/{self.tailnet}/devices")
        resp.raise_for_status()
        return True

    def get_devices(self) -> list:
        resp = self.client.get(f"{self.base_url}/tailnet/{self.tailnet}/devices")
        resp.raise_for_status()
        data = resp.json()
        return data.get("devices", [])

    def sync(self) -> bool:
        start_time = time.time()
        logger.info(f"Tailscale sync starting for tailnet: {self.tailnet}...")

        try:
            ts_devices = self.get_devices()
            conn = get_connection()
            updated_count = 0

            try:
                for dev in ts_devices:
                    # Prefer IPv4, fallback to first address
                    addresses = dev.get("addresses", [])
                    if not addresses:
                        continue
                    
                    ip = None
                    for addr in addresses:
                        if "." in addr:
                            ip = addr
                            break
                    if not ip:
                        ip = addresses[0]

                    hostname = dev.get("hostname", "")
                    os_name = dev.get("os", "")
                    ts_name = dev.get("name", "")
                    last_seen_str = dev.get("lastSeen", "")
                    
                    provider = "tailscale"
                    node_id = dev.get("nodeId", "")
                    client_version = dev.get("clientVersion", "")
                    
                    from app.core.date_utils import parse_iso_utc
                    try:
                        last_seen_dt = parse_iso_utc(last_seen_str)
                    except:
                        last_seen_dt = utc_now()
                        
                    # Upsert based on node_id
                    row = conn.execute("SELECT id FROM vpn_nodes WHERE node_id = ? AND provider = ?", [node_id, provider]).fetchone()
                    
                    if not row:
                        device_id = str(uuid.uuid4())
                        conn.execute(
                            """
                            INSERT INTO vpn_nodes (id, provider, node_id, ip, hostname, os, client_version, last_seen, status, is_trusted)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'online', FALSE)
                            """,
                            [device_id, provider, node_id, ip, hostname or ts_name, os_name, client_version, last_seen_dt]
                        )
                    else:
                        device_id = row[0]
                        conn.execute(
                            """
                            UPDATE vpn_nodes 
                            SET ip = ?, hostname = COALESCE(NULLIF(hostname, ''), ?), os = ?, client_version = ?, last_seen = ?, status = 'online'
                            WHERE id = ?
                            """,
                            [ip, hostname or ts_name, os_name, client_version, last_seen_dt, device_id]
                        )
                        
                    updated_count += 1
                
                conn.commit()
                logger.info(f"Tailscale sync complete: {updated_count} devices updated")
                
            finally:
                conn.close()

            duration = int((time.time() - start_time) * 1000)
            log_task_event(
                task_type="tailscale_sync",
                event_type="completed",
                message=f"Tailscale sync completed. {updated_count} devices found/updated.",
                target="tailscale",
                duration_ms=duration,
                details={"devices_count": len(ts_devices), "updated_devices": updated_count},
            )
            return True

        except Exception as e:
            logger.error(f"Tailscale sync failed: {e}", exc_info=True)
            duration = int((time.time() - start_time) * 1000)
            log_task_event(
                task_type="tailscale_sync",
                event_type="failed",
                message=f"Tailscale sync failed: {str(e)}",
                target="tailscale",
                duration_ms=duration,
                level="ERROR",
            )
            raise
