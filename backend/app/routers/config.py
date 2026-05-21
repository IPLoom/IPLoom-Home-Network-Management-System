from fastapi import APIRouter
from app.core.db import get_connection
from app.models.config import ConfigItem, ConfigUpdate
import asyncio
import json
from typing import Any
from app.services.mqtt import MQTTManager
import logging

from app.services.discovery import DiscoveryService

logger = logging.getLogger(__name__)
router = APIRouter()
public_router = APIRouter()

@public_router.get("/discover")
async def discover_network():
    """Attempt to auto-detect local network configuration and services (cached)."""
    return await DiscoveryService.get_cached_discovery()

@router.get("/", response_model=list[ConfigItem])
async def list_config():
    def query():
        conn = get_connection()
        try:
            rows = conn.execute("SELECT key, value FROM config").fetchall()
            return [ConfigItem(key=r[0], value=r[1] or "") for r in rows]
        finally:
            conn.close()
    return await asyncio.to_thread(query)

@router.get("/{key}", response_model=ConfigItem)
async def get_config_item(key: str):
    def query():
        conn = get_connection()
        try:
            row = conn.execute("SELECT key, value FROM config WHERE key = ?", [key]).fetchone()
            if not row:
                return ConfigItem(key=key, value="")
            return ConfigItem(key=row[0], value=row[1] or "")
        finally:
            conn.close()
    return await asyncio.to_thread(query)

@router.put("/{key}", response_model=ConfigItem)
async def upsert_config_item(key: str, payload: ConfigUpdate):
    def update():
        conn = get_connection()
        try:
            conn.execute(
                """
                INSERT OR REPLACE INTO config (key, value, updated_at)
                VALUES (?, ?, now())
                """,
                [key, payload.value],
            )
            conn.commit()
            logger.info(f"Updated config {key} to {payload.value}")
        finally:
            conn.close()
    await asyncio.to_thread(update)
    return ConfigItem(key=key, value=payload.value)

@router.post("/", response_model=list[ConfigItem])
async def bulk_update_config(payload: dict[str, Any]):
    def update():
        conn = get_connection()
        results = []
        mqtt_changed = False
        try:
            for key, value in payload.items():
                if key.startswith("mqtt_"):
                    mqtt_changed = True
                    
                if not isinstance(value, str):
                    val_str = json.dumps(value)
                else:
                    val_str = value
                    
                conn.execute(
                    """
                    INSERT OR REPLACE INTO config (key, value, updated_at)
                    VALUES (?, ?, now())
                    """,
                    [key, val_str],
                )
                results.append(ConfigItem(key=key, value=val_str))
            conn.commit()
            logger.info(f"Bulk updated {len(payload)} config items")
            return results, mqtt_changed
        finally:
            conn.close()
            
    results, mqtt_changed = await asyncio.to_thread(update)
    
    if mqtt_changed:
        logger.info("MQTT settings changed, reconnecting persistent client...")
        # Reconnect the persistent client with updated config so the live
        # connection immediately uses the new broker/credentials.
        def reconnect_mqtt():
            MQTTManager.get_instance().reconnect()
            
        await asyncio.to_thread(reconnect_mqtt)
        
    return results
