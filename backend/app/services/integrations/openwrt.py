
import logging
import requests
import json
import os
import re
from base64 import b64encode
from datetime import datetime, timezone
from app.core.date_utils import now as utc_now, parse_iso_utc
from app.core.config import get_settings
from app.core.db import get_connection
from app.core.task_logger import log_task_event
import time

logger = logging.getLogger(__name__)

def sanitize_hostname(name: str) -> str:
    if not name:
        return ""
    # Replace any character that is not alphanumeric or hyphen with a hyphen
    sanitized = re.sub(r'[^a-zA-Z0-9-]', '-', name)
    # Replace multiple consecutive hyphens with a single hyphen
    sanitized = re.sub(r'-+', '-', sanitized)
    # Strip leading and trailing hyphens
    sanitized = sanitized.strip('-')
    # Limit length to 63 chars
    return sanitized[:63].lower()

class OpenWRTClient:
    def __init__(self, base_url, username, password=None):
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.token = None
        self.session = requests.Session()

        # No longer using local config file, state is in DB

    def login(self):
        """Authenticate with OpenWRT via ubus session login"""
        if self.token:
            return

        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "call",
            "params": [
                "00000000000000000000000000000000",
                "session",
                "login",
                {
                    "username": self.username,
                    "password": self.password or ""
                }
            ]
        }
        
        try:
            resp = self.session.post(f"{self.base_url}/ubus", json=payload, timeout=10)
            data = resp.json()
            
            if "result" in data and isinstance(data["result"], list) and len(data["result"]) > 1:
                status, session_data = data["result"]
                if status == 0 and isinstance(session_data, dict) and "ubus_rpc_session" in session_data:
                    self.token = session_data["ubus_rpc_session"]
                    logger.info("OpenWRT Login successful")
                    return
            
            logger.error(f"OpenWRT login failed. Response: {data}")
            raise Exception("Login failed: Invalid credentials or response format")
            
        except Exception as e:
            logger.error(f"Failed to connect to OpenWRT: {e}")
            raise e

    def _call(self, object, method, params=None, optional=False):
        """Invoke a ubus method with standard error handling and retries"""
        if not self.token:
            self.login()
        
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "call",
            "params": [
                self.token,
                object,
                method,
                params or {}
            ]
        }
        
        try:
            resp = self.session.post(f"{self.base_url}/ubus", json=payload, timeout=10)
            data = resp.json()
            
            if "result" in data and isinstance(data["result"], list):
                status = data["result"][0]
                
                if status == 0:
                    if len(data["result"]) > 1:
                        return data["result"][1]
                    return [] 
                
                if status == 6: # Permission denied / Session expired
                    logger.warning(f"OpenWRT Permission Denied (6) for {object}.{method}. Retrying login...")
                    self.token = None
                    self.login()
                    
                    payload["params"][0] = self.token
                    resp = self.session.post(f"{self.base_url}/ubus", json=payload, timeout=10)
                    data = resp.json()
                    
                    if data and "result" in data and isinstance(data["result"], list) and data["result"][0] == 0:
                        return data["result"][1] if len(data["result"]) > 1 else []
                
                if not optional:
                    logger.error(f"OpenWRT RPC Error {status} for {object}.{method}")
                return [] if optional else None

            if "error" in data:
                logger.error(f"OpenWRT JSON-RPC Error: {data['error']}")
                return [] if optional else None
                
            return [] if optional else None
            
        except Exception as e:
            logger.error(f"OpenWRT Call Exception ({object}.{method}): {e}")
            return [] if optional else None

    def get_dhcp_leases(self):
        """Get DHCP leases using luci-rpc.getDHCPLeases"""
        res = self._call("luci-rpc", "getDHCPLeases", optional=True)
        
        leases = []
        if isinstance(res, dict) and "dhcp_leases" in res:
            for item in res["dhcp_leases"]:
                leases.append({
                    "ip": item.get("ipaddr"),
                    "mac": item.get("macaddr"),
                    "hostname": item.get("hostname", "*"),
                    "expires": item.get("expires", 0)
                })
        return leases

    def get_wireless_devices(self):
        """Get wireless associations using luci-rpc.getWirelessDevices"""
        res = self._call("luci-rpc", "getWirelessDevices", optional=True)
        
        associations = {}
        if isinstance(res, dict):
            for interface, data in res.items():
                if not isinstance(data, dict): continue
                
                # Infer band from frequency or interface name
                freq = str(data.get("frequency", "")).lower()
                band = "2.4GHz" if "2.4" in freq else ("5GHz" if "5" in freq or "6" in freq else "Unknown")
                ssid = data.get("ssid", "Unknown")
                
                assoc_list = data.get("associations", [])
                for assoc in assoc_list:
                    mac = assoc.get("mac", "").lower()
                    if mac:
                        associations[mac] = {
                            "rssi": assoc.get("signal"),
                            "noise": assoc.get("noise"),
                            "rx_rate": assoc.get("rx_rate"),
                            "tx_rate": assoc.get("tx_rate"),
                            "band": band,
                            "ssid": ssid,
                            "interface": interface
                        }
        return associations

    def get_traffic_stats(self):
        """Get traffic data and calculate deltas using /usr/sbin/nlbw"""
        stats = {}
        
        res = self._call("file", "exec", {
            "command": "/usr/sbin/nlbw", 
            "params": ["-c", "json", "-g", "mac,fam", "-o", "conn"]
        }, optional=True)
        
        if isinstance(res, dict) and "stdout" in res:
            try:
                data = json.loads(res["stdout"])
                rows = data.get("data", [])
                for row in rows:
                    if len(row) >= 6: 
                        mac = row[1].lower()
                        if not mac or mac == "00:00:00:00:00:00": continue
                        
                        rx = int(row[3]) 
                        tx = int(row[5]) 
                        
                        if mac not in stats:
                            stats[mac] = {"down": 0, "up": 0}
                        stats[mac]["down"] += rx
                        stats[mac]["up"] += tx
            except Exception as e:
                logger.error(f"Failed to calculate traffic stats: {e}")

        traffic_data = self._calculate_deltas(stats)
        return traffic_data

    def get_arp_table(self):
        """Retrieve local ARP table from the OpenWRT router using getHostHints."""
        logger.info("OpenWRT: Fetching ARP table via getHostHints...")
        res = self._call("luci-rpc", "getHostHints", optional=True)
        
        arp_entries = {}
        if isinstance(res, dict):
            for mac, info in res.items():
                if not isinstance(info, dict):
                    continue
                ipaddrs = info.get("ipaddrs")
                ip = ipaddrs[0] if ipaddrs and isinstance(ipaddrs, list) else None
                mac_lower = mac.lower()
                if ip and mac_lower and mac_lower != "00:00:00:00:00:00" and len(mac_lower) == 17:
                    arp_entries[ip] = mac_lower
        
        logger.info(f"OpenWRT: Found {len(arp_entries)} entries in ARP table via getHostHints.")
        return arp_entries

    def _calculate_deltas(self, current_stats):
        """Calculates usage since last sync using a local cache file"""
        cache_file = "data/openwrt_stats.json"
        prev_stats = {}
        
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    prev_stats = json.load(f)
            except:
                pass
        
        deltas = {}
        for mac, curr in current_stats.items():
            if mac not in prev_stats:
                # First time seeing this device (or cache lost). 
                # value is cumulative, so we can't determine usage since last sync.
                # Treat as 0 delta to avoid massive spikes (e.g. 60GB) being logged.
                deltas[mac] = {"down": 0, "up": 0}
                continue

            prev = prev_stats[mac]
            
            # Normal case: Calculate diff
            # Handle restart (curr < prev): assume curr is all new traffic (reset)
            down_delta = curr["down"] - prev["down"] if curr["down"] >= prev["down"] else curr["down"]
            up_delta = curr["up"] - prev["up"] if curr["up"] >= prev["up"] else curr["up"]
            
            deltas[mac] = {"down": down_delta, "up": up_delta}
        
        try:
             os.makedirs("data", exist_ok=True)
             with open(cache_file, 'w') as f:
                 json.dump(current_stats, f)
        except:
             pass
             
        return {"deltas": deltas, "totals": current_stats}

    def sync(self, force: bool = False):
        """Pull data and update DB: DHCP Leases = Dynamic, Others = Static"""
        os.makedirs("data", exist_ok=True) # Ensure data directory exists for config file



        logger.info("Starting OpenWRT Sync...")
        log_task_event(
            task_type="openwrt_sync", 
            event_type="started", 
            message="Starting OpenWRT sync", 
            target="openwrt"
        )
        
        start_time = time.time()

        try:
            self.login()
            
            # Fetch integration config to see if wireless query should be skipped
            is_ap = True
            conn_temp = get_connection()
            try:
                row = conn_temp.execute("SELECT config FROM integrations WHERE name = 'openwrt'").fetchone()
                if row:
                    try:
                        integration_conf = json.loads(row[0])
                        is_ap = integration_conf.get("is_access_point", True)
                    except:
                        pass
            finally:
                conn_temp.close()
            
            leases = self.get_dhcp_leases()
            static_leases = self.get_static_leases()
            wireless_assoc = self.get_wireless_devices() if is_ap else {}
            traffic_data = self.get_traffic_stats()
            traffic_deltas = traffic_data["deltas"]
            traffic_totals = traffic_data["totals"]
            arp_map = self.get_arp_table()
            
            conn = get_connection()
            try:
                updated_count = 0
                
                # 1. Build a map of current DHCP leases
                dhcp_map = {} # mac -> lease
                for l in leases:
                    if l.get("mac"):
                        dhcp_map[l["mac"].lower()] = l

                # Add ARP entries to our DHCP map for static devices
                for ip, mac in arp_map.items():
                    mac_lower = mac.lower()
                    if mac_lower not in dhcp_map:
                        dhcp_map[mac_lower] = {
                            "ip": ip,
                            "mac": mac_lower,
                            "hostname": None,
                            "expires": 0
                        }

                # 2. Get set of ALL MACs involved (Traffic + DHCP + Wireless)
                all_macs = set(dhcp_map.keys())
                all_macs.update(traffic_totals.keys())
                all_macs.update(wireless_assoc.keys())

                for mac in all_macs:
                    mac = mac.lower()
                    lease = dhcp_map.get(mac)
                    
                    t_delta = traffic_deltas.get(mac, {"down": 0, "up": 0})
                    t_total = traffic_totals.get(mac, {"down": 0, "up": 0})
                    
                    # Skip if no useful data (no lease and no traffic)
                    if not lease and t_total["down"] == 0 and t_total["up"] == 0:
                        continue

                    row = conn.execute("SELECT id, name, display_name, icon, attributes, ip, ip_type, mac FROM devices WHERE mac = ?", [mac]).fetchone()
                    if not row:
                        row = conn.execute("SELECT id, name, display_name, icon, attributes, ip, ip_type, mac FROM devices WHERE id = ?", [mac]).fetchone()
                    
                    # Fallback: if scanner found it but couldn't get MAC, try mapping by IP
                    if not row and lease and lease.get("ip"):
                        row = conn.execute("SELECT id, name, display_name, icon, attributes, ip, ip_type, mac FROM devices WHERE ip = ?", [lease["ip"]]).fetchone()

                    if not row:
                        continue
                    
                    target_id = row[0]
                    existing_name = row[1]
                    existing_icon = row[3]
                    try:
                        attrs = json.loads(row[4]) if row[4] else {}
                    except:
                        attrs = {}
                    existing_ip = row[5]
                    existing_ip_type = row[6]
                    existing_mac = row[7]

                    # Determine IP and IP Type
                    if mac in static_leases:
                        ip_type = "reserved"
                        ip = lease["ip"] if lease else static_leases[mac]["ip"]
                        hostname = static_leases[mac].get("name") or (lease["hostname"] if lease else None)
                    elif lease and lease.get("expires", 0) > 0:
                        ip = lease["ip"]
                        ip_type = "dynamic"
                        hostname = lease["hostname"] if lease["hostname"] and lease["hostname"] != "*" else None
                        attrs["dhcp_expires"] = lease["expires"]
                        if hostname: attrs["dhcp_hostname"] = hostname
                    else:
                        # Static / No Lease - use existing DB info if it's already set to a valid state
                        ip = lease["ip"] if lease else existing_ip
                        ip_type = existing_ip_type if existing_ip_type in ("static", "dynamic", "reserved") else "static"
                        hostname = lease["hostname"] if lease else None

                    # Use lease hostname if available
                    name = existing_name or hostname or f"Device-{mac[-5:]}"
                    
                    attrs["last_sync"] = "openwrt"
                    
                    # Add Wireless Details
                    wlan = wireless_assoc.get(mac)
                    if wlan:
                        attrs["wlan_rssi"] = wlan["rssi"]
                        attrs["wlan_band"] = wlan["band"]
                        attrs["wlan_ssid"] = wlan["ssid"]
                        attrs["wlan_rx_rate"] = wlan["rx_rate"]
                        attrs["wlan_tx_rate"] = wlan["tx_rate"]
                        attrs["connection_type"] = "wireless"
                    else:
                        # Clean up active wireless link stats when not associated
                        attrs.pop("wlan_rssi", None)
                        attrs.pop("wlan_band", None)
                        attrs.pop("wlan_ssid", None)
                        attrs.pop("wlan_rx_rate", None)
                        attrs.pop("wlan_tx_rate", None)
                        
                        # Smart preservation and intrinsic classification fallbacks
                        existing_conn_type = attrs.get("connection_type")
                        display_name = row[2] if row else None
                        
                        intrinsically_wireless = False
                        combined_str = f"{mac} {hostname or ''} {name or ''} {display_name or ''}".lower()
                        wireless_kws = [
                            "wiz", "bulb", "tasmota", "esphome", "esp32", "esp8266", "shelly", "sonoff",
                            "smart", "plug", "camera", "phone", "tablet", "mobile", "deco", "motion",
                            "motor-controller", "labbulb", "dining-motion", "android", "iphone", "ipad",
                            "galaxy", "pixel", "oneplus", "xiaomi", "huawei", "television", "smarttv"
                        ]
                        if any(kw in combined_str for kw in wireless_kws):
                            intrinsically_wireless = True
                            
                        if existing_conn_type == "wireless" or intrinsically_wireless:
                            attrs["connection_type"] = "wireless"
                        elif lease:
                            attrs["connection_type"] = "wired"
                    
                    # Insert into history (Always record traffic if available)
                    if t_total["down"] > 0 or t_total["up"] > 0:
                        import uuid
                        hist_id = str(uuid.uuid4())
                        try:
                            conn.execute("""
                                INSERT INTO device_traffic_history 
                                (id, device_id, rx_bytes, tx_bytes, down_rate, up_rate) 
                                VALUES (?, ?, ?, ?, ?, ?)
                            """, [hist_id, target_id, t_total["down"], t_total["up"], t_delta["down"], t_delta["up"]])
                            
                            # Increment Quota Usage if defined
                            delta_total = t_delta["down"] + t_delta["up"]
                            if delta_total > 0:
                                conn.execute("""
                                    UPDATE device_quotas 
                                    SET current_usage = current_usage + ? 
                                    WHERE device_id = ? AND enabled = TRUE
                                """, [delta_total, target_id])
                        except Exception as e:
                             logger.error(f"Failed to insert traffic history or update quota for {mac}: {e}")

                    # Update Device Table
                    if row:
                        try:
                             conn.execute("""
                                UPDATE devices SET
                                    mac = COALESCE(mac, ?),
                                    ip = COALESCE(?, ip),
                                    ip_type = ?
                                WHERE id = ?
                            """, [mac, ip, ip_type, target_id])
                             
                             conn.execute("""
                                 INSERT OR REPLACE INTO device_discovery_sources (device_id, source, last_seen, status, attributes)
                                 VALUES (?, 'openwrt', ?, 'online', ?)
                             """, [target_id, utc_now(), json.dumps(attrs)])
                             
                             from app.services.devices import recalculate_device_status
                             recalculate_device_status(conn, target_id)
                             
                             updated_count += 1
                        except Exception as e:
                            logger.error(f"Failed to update device {mac}: {e}")
                
                conn.commit()
                logger.info(f"OpenWRT Sync complete: {updated_count} devices processed.")
                
            finally:
                conn.close()
            
            # Update last_sync and last_run in DB
            try:
                # Read current config from DB
                conn_main = get_connection()
                try:
                    row = conn_main.execute("SELECT config FROM integrations WHERE name = 'openwrt'").fetchone()
                    if row:
                        current_config = json.loads(row[0])
                        current_config["last_sync"] = utc_now().isoformat()
                        current_config["last_run"] = utc_now().isoformat()
                        conn_main.execute("UPDATE integrations SET config = ? WHERE name = 'openwrt'", [json.dumps(current_config)])
                        from app.core.db import commit
                        commit()
                finally:
                    conn_main.close()
            except Exception as e:
                logger.error(f"Failed to update OpenWRT timestamps in DB: {e}")

            duration = int((time.time() - start_time) * 1000)
            logger.info(f"OpenWRT Sync complete: {len(leases)} leases processed.")
            
            log_task_event(
                task_type="openwrt_sync", 
                event_type="completed", 
                message=f"OpenWRT sync completed. Processed {len(leases)} leases.", 
                target="openwrt",
                duration_ms=duration,
                details={"leases_count": len(leases), "updated_devices": updated_count}
            )
            
            return True
                
        except Exception as e:
            logger.error(f"OpenWRT Sync Failed: {e}", exc_info=True)
            
            log_task_event(
                task_type="openwrt_sync", 
                event_type="failed", 
                message=f"OpenWRT sync failed: {str(e)}", 
                target="openwrt",
                level="ERROR",
                details={"error": str(e)}
            )
            
            raise e

    def block_device(self, mac: str):
        """Block a device by MAC address using OpenWrt firewall (uci)."""
        logger.info(f"OpenWRT: Blocking device {mac}")
        mac = mac.lower()
        sanitized_mac = mac.replace(':', '')
        rule_name = f"block_{sanitized_mac}"
        
        # Create the section if it doesn't exist
        self._call("uci", "add", {
            "config": "firewall",
            "type": "rule",
            "name": rule_name
        }, optional=True)
        
        # Update the named firewall rule section
        # Using DROP and ensuring both IPv4/IPv6 coverage
        self._call("uci", "set", {
            "config": "firewall",
            "type": "rule",
            "section": rule_name,
            "values": {
                "name": f"IPLoom_Block_{sanitized_mac}",
                "src": "lan",
                "dest": "wan",
                "src_mac": mac,
                "target": "DROP",
                "enabled": "1"
            }
        }, optional=False)
        
        # Commit the changes
        self._call("uci", "commit", {"config": "firewall"}, optional=False)
        
        # Move rule to top of the list to ensure it overrides 'Allow Established' logic
        self._call("file", "exec", {
            "command": "/sbin/uci",
            "params": ["insert", f"firewall.{rule_name}=0"]
        }, optional=True)
        self._call("uci", "commit", {"config": "firewall"}, optional=True)

        # Reload firewall for immediate effect on new connections
        # We use reload instead of apply to be more aggressive with ruleset rebuild
        self._call("file", "exec", {
            "command": "/etc/init.d/firewall",
            "params": ["reload"]
        }, optional=True)

        # CRITICAL: Flush established connections for this device
        # Otherwise streaming/existing sessions continue until timeout
        try:
            leases = self.get_dhcp_leases()
            ip = next((l["ip"] for l in leases if l["mac"].lower() == mac.lower()), None)
            if ip:
                logger.info(f"OpenWRT: Flushing conntrack for IP {ip}")
                # Clear all states where this IP is source or destination
                self._call("file", "exec", {
                    "command": "/usr/sbin/conntrack",
                    "params": ["-D", "-s", ip]
                }, optional=True)
                self._call("file", "exec", {
                    "command": "/usr/sbin/conntrack",
                    "params": ["-D", "-d", ip]
                }, optional=True)
        except Exception as e:
            logger.warning(f"Could not flush conntrack for {mac}: {e}")
        
        return True

    def unblock_device(self, mac: str):
        """Unblock a device by MAC address using OpenWrt firewall (uci)."""
        logger.info(f"OpenWRT: Unblocking device {mac}")
        mac = mac.lower()
        sanitized_mac = mac.replace(':', '')
        rule_name = f"block_{sanitized_mac}"
        
        # Delete the section
        res = self._call("uci", "delete", {
            "config": "firewall",
            "section": rule_name
        }, optional=True)
        
        # Commit the changes
        self._call("uci", "commit", {"config": "firewall"}, optional=True)
        
        # Reload firewall
        self._call("file", "exec", {
            "command": "/etc/init.d/firewall",
            "params": ["reload"]
        }, optional=True)
        
        return res

    def get_static_leases(self):
        """Get configured static leases from UCI dhcp config"""
        res = self._call("file", "exec", {
            "command": "/sbin/uci",
            "params": ["show", "dhcp"]
        }, optional=True)
        
        leases = {}
        if isinstance(res, dict) and "stdout" in res:
            import re
            lines = res["stdout"].splitlines()
            sections = {}
            for line in lines:
                m = re.match(r"dhcp\.([^.]+)\.([^=]+)='?([^']+)'?", line)
                if m:
                    sec_name, option, value = m.groups()
                    if sec_name not in sections:
                        sections[sec_name] = {}
                    sections[sec_name][option] = value
                else:
                    m2 = re.match(r"dhcp\.([^=]+)=host", line)
                    if m2:
                        sec_name = m2.group(1)
                        if sec_name not in sections:
                            sections[sec_name] = {}
                            
            for sec_name, opts in sections.items():
                mac = opts.get("mac")
                ip = opts.get("ip")
                if mac and ip:
                    leases[mac.lower()] = {
                        "ip": ip,
                        "name": opts.get("name"),
                        "section": sec_name
                    }
        return leases

    def reserve_ip(self, mac: str, ip: str, hostname: str = None):
        """Add or update a static DHCP lease for a MAC address on OpenWrt."""
        logger.info(f"OpenWRT: Reserving IP {ip} for MAC {mac}")
        mac = mac.lower()
        if hostname:
            hostname = sanitize_hostname(hostname)
        if not hostname:
            hostname = f"device-{mac.replace(':', '')[-4:]}"
        
        # 1. Fetch existing static leases and validate
        existing_leases = self.get_static_leases()
        
        # Validation 1: IP address conflict with another device
        for existing_mac, lease in existing_leases.items():
            if existing_mac != mac and lease["ip"] == ip:
                raise ValueError(f"IP address {ip} is already reserved for another device ({existing_mac}).")
                
        # Validation 2: MAC address already has a reservation
        if mac in existing_leases:
            existing_lease = existing_leases[mac]
            if existing_lease["ip"] == ip:
                raise ValueError(f"A static IP reservation of {ip} already exists for this device on the router.")
            else:
                raise ValueError(f"This device already has a static IP reservation for {existing_lease['ip']}. Please release/unreserve it first.")

        sanitized_mac = mac.replace(':', '')
        section_name = f"lease_{sanitized_mac}"
        
        # 2. Clean up any lingering leases matching the MAC (just in case)
        self._call("file", "exec", {
            "command": "/bin/sh",
            "params": ["-c", f"for sec in $(uci show dhcp | grep -i '{mac}' | cut -d. -f2 | cut -d= -f1); do uci delete dhcp.$sec; done"]
        }, optional=True)
        
        # 3. Create the named host section
        self._call("uci", "add", {
            "config": "dhcp",
            "type": "host",
            "name": section_name
        }, optional=True)
        
        # 4. Update the named host section values
        self._call("uci", "set", {
            "config": "dhcp",
            "type": "host",
            "section": section_name,
            "values": {
                "name": hostname,
                "mac": mac,
                "ip": ip
            }
        }, optional=False)
        
        # 5. Commit the changes
        self._call("uci", "commit", {"config": "dhcp"}, optional=False)
        
        # 6. Reload dnsmasq for immediate effect
        self._call("file", "exec", {
            "command": "/etc/init.d/dnsmasq",
            "params": ["reload"]
        }, optional=True)
        
        return True

    def unreserve_ip(self, mac: str):
        """Remove any static DHCP leases for a MAC address on OpenWrt."""
        logger.info(f"OpenWRT: Removing IP reservation for MAC {mac}")
        mac = mac.lower()
        
        # 1. Clean up any leases matching the MAC
        self._call("file", "exec", {
            "command": "/bin/sh",
            "params": ["-c", f"for sec in $(uci show dhcp | grep -i '{mac}' | cut -d. -f2 | cut -d= -f1); do uci delete dhcp.$sec; done"]
        }, optional=True)
        
        # 2. Commit the changes
        self._call("uci", "commit", {"config": "dhcp"}, optional=True)
        
        # 3. Reload dnsmasq
        self._call("file", "exec", {
            "command": "/etc/init.d/dnsmasq",
            "params": ["reload"]
        }, optional=True)
        
        return True


