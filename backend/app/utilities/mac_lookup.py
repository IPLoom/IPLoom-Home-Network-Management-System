import httpx
import logging
import time
import asyncio
from typing import Optional

logger = logging.getLogger(__name__)

_last_macvendors_rate_limit_time = 0.0
_last_maclookup_rate_limit_time = 0.0
_last_request_time = 0.0
_request_lock = asyncio.Lock()
ENRICHMENT_COOLDOWN = 300  # 5 minutes
REQUEST_INTERVAL = 1.2    # Throttling interval in seconds to prevent 429s

async def get_vendor_from_api(mac: str) -> Optional[str]:
    """
    Fetches vendor name for a MAC address using multiple external APIs.
    Includes separate 5-minute cool-downs for each service if they return a 429 Rate Limit.
    Throttles concurrent requests to keep a spacing of at least REQUEST_INTERVAL seconds.
    """
    global _last_macvendors_rate_limit_time, _last_maclookup_rate_limit_time, _last_request_time
    
    now = time.time()
    macvendors_cooldown = (now - _last_macvendors_rate_limit_time < ENRICHMENT_COOLDOWN)
    maclookup_cooldown = (now - _last_maclookup_rate_limit_time < ENRICHMENT_COOLDOWN)
    
    if macvendors_cooldown and maclookup_cooldown:
        logger.debug(f"Skipping external enrichment for {mac} because both APIs are in rate-limit cool-down.")
        return None

    # Throttling delay
    async with _request_lock:
        now_time = time.time()
        elapsed = now_time - _last_request_time
        if elapsed < REQUEST_INTERVAL:
            delay = REQUEST_INTERVAL - elapsed
            logger.debug(f"Throttling MAC lookup for {mac}, sleeping for {delay:.2f}s")
            await asyncio.sleep(delay)
        _last_request_time = time.time()

    async with httpx.AsyncClient() as client:
        # 1. Primary: macvendors.com
        if not macvendors_cooldown:
            try:
                resp = await client.get(f"https://api.macvendors.com/{mac}", timeout=5.0)
                if resp.status_code == 200:
                    return resp.text.strip()
                elif resp.status_code == 429:
                    logger.warning(f"Rate limited by macvendors.com for {mac}. Engaging 5-minute cool-down for macvendors.com.")
                    _last_macvendors_rate_limit_time = time.time()
                else:
                    logger.debug(f"macvendors.com returned status {resp.status_code} for {mac}")
            except Exception as e:
                logger.warning(f"macvendors.com request failed for {mac}: {e}")

        # 2. Fallback: maclookup.app
        if not maclookup_cooldown:
            try:
                resp = await client.get(f"https://api.maclookup.app/v2/macs/{mac}", timeout=5.0)
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("success") and data.get("company"):
                        return data["company"]
                elif resp.status_code == 429:
                    logger.warning(f"Rate limited by maclookup.app for {mac}. Engaging 5-minute cool-down for maclookup.app.")
                    _last_maclookup_rate_limit_time = time.time()
                else:
                    logger.debug(f"maclookup.app returned status {resp.status_code} for {mac}")
            except Exception as e:
                logger.warning(f"maclookup.app request failed for {mac}: {e}")

    return None


