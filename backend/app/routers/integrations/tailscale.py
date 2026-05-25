import json
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, Dict, Any

from app.core.db import get_connection
from app.services.integrations.tailscale import TailscaleClient
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class TailscaleConfig(BaseModel):
    api_key: str
    tailnet: Optional[str] = "-"
    enabled: bool = True

@router.get("/config")
def get_config():
    """Get the current Tailscale configuration."""
    conn = get_connection()
    try:
        row = conn.execute("SELECT config FROM integrations WHERE name = 'tailscale'").fetchone()
        if row and row[0]:
            return json.loads(row[0])
        return {"api_key": "", "tailnet": "-", "enabled": False}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@router.post("/config")
def save_config(config: TailscaleConfig):
    """Save the Tailscale configuration."""
    conn = get_connection()
    try:
        conn.execute(
            "INSERT OR REPLACE INTO integrations (name, config) VALUES ('tailscale', ?)",
            [json.dumps(config.model_dump())]
        )
        conn.commit()
        return {"status": "success", "message": "Tailscale config saved"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@router.post("/verify")
def verify_credentials(config: TailscaleConfig):
    """Verify Tailscale API credentials."""
    try:
        client = TailscaleClient(config.api_key, config.tailnet)
        client.verify()
        return {"status": "success", "message": "Connection verified"}
    except Exception as e:
        logger.error(f"Tailscale verification failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/sync")
def sync_now(background_tasks: BackgroundTasks):
    """Trigger a manual sync of Tailscale devices."""
    conn = get_connection()
    try:
        row = conn.execute("SELECT config FROM integrations WHERE name = 'tailscale'").fetchone()
        if not row or not row[0]:
            raise HTTPException(status_code=404, detail="Tailscale not configured")
            
        config = json.loads(row[0])
        if not config.get("enabled", False):
            raise HTTPException(status_code=400, detail="Tailscale integration is disabled")
            
        client = TailscaleClient(config["api_key"], config["tailnet"])
        
        # Run sync in background so we don't block the API request
        background_tasks.add_task(client.sync)
        
        return {"status": "success", "message": "Sync started in the background"}
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

class VpnNodeUpdate(BaseModel):
    is_trusted: Optional[bool] = None

@router.get("/devices")
def get_devices():
    """Get all Tailscale VPN nodes."""
    conn = get_connection()
    try:
        rows = conn.execute("SELECT id, node_id, ip, hostname, os, client_version, last_seen, status, is_trusted FROM vpn_nodes WHERE provider = 'tailscale'").fetchall()
        devices = []
        for r in rows:
            devices.append({
                "id": r[0],
                "node_id": r[1],
                "ip": r[2],
                "name": r[3],
                "display_name": r[3],
                "os": r[4],
                "client_version": r[5],
                "last_seen": r[6].isoformat() if r[6] else None,
                "status": r[7],
                "is_trusted": r[8]
            })
        return devices
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@router.patch("/devices/{device_id}")
def update_device(device_id: str, update: VpnNodeUpdate):
    """Update a Tailscale VPN node (e.g., trust status)."""
    conn = get_connection()
    try:
        if update.is_trusted is not None:
            conn.execute("UPDATE vpn_nodes SET is_trusted = ? WHERE id = ?", [update.is_trusted, device_id])
            conn.commit()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@router.delete("/devices/{device_id}")
def delete_device(device_id: str):
    """Delete a Tailscale VPN node."""
    conn = get_connection()
    try:
        conn.execute("DELETE FROM vpn_nodes WHERE id = ?", [device_id])
        conn.commit()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()
