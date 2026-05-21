"""
TP-Link Deco Mesh Client — Pure Python implementation using httpx.
Reverse-engineered from community implementations (ha-tplink-deco, mrmarble/deco).
No third-party TP-Link libraries used.
"""

import logging
import json
import hashlib
import time
import uuid
import secrets
import base64
import urllib.parse
import httpx
from cryptography.hazmat.primitives.asymmetric import rsa as crypto_rsa
from cryptography.hazmat.primitives.asymmetric import padding as crypto_padding
from cryptography.hazmat.primitives import padding as symmetric_padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from app.core.db import get_connection, commit
from app.core.date_utils import now as utc_now
from app.core.task_logger import log_task_event

logger = logging.getLogger(__name__)

# Deco CGI base path
CGI_PATH = "/cgi-bin/luci/;stok="


def decode_deco_name(name_str: str) -> str:
    if not name_str:
        return name_str
    # TP-Link Deco API names are base64-encoded if they contain special characters or spaces.
    # Attempt to decode if it is a valid base64 string and check if the decoded bytes
    # form a valid UTF-8 string consisting of printable characters.
    try:
        missing_padding = len(name_str) % 4
        padded_str = name_str
        if missing_padding:
            padded_str += "=" * (4 - missing_padding)
        
        decoded_bytes = base64.b64decode(padded_str, validate=True)
        decoded_str = decoded_bytes.decode("utf-8", errors="strict")
        
        # Ensure the decoded string is printable and has no control/garbage characters
        if decoded_str.isprintable() and len(decoded_str) > 0:
            return decoded_str
    except Exception:
        pass
    return name_str


def rsa_encrypt(n: int, e: int, plaintext: bytes) -> str:
    """RSA encrypt using cryptography library with PKCS#1 v1.5 padding."""
    pubkey = crypto_rsa.RSAPublicNumbers(e, n).public_key()
    block_size = (n.bit_length() + 7) // 8
    bytes_per_block = block_size - 11  # PKCS1 v1.5 padding overhead
    
    encrypted_hex = ""
    text_bytes = len(plaintext)
    index = 0
    while index < text_bytes:
        content_num_bytes = min(bytes_per_block, text_bytes - index)
        content = plaintext[index : index + content_num_bytes]
        encrypted_block = pubkey.encrypt(content, crypto_padding.PKCS1v15())
        encrypted_hex += encrypted_block.hex()
        index += content_num_bytes
    return encrypted_hex


def aes_encrypt(key: bytes, iv: bytes, plaintext: bytes) -> bytes:
    """AES CBC encrypt with PKCS#7 padding."""
    padder = symmetric_padding.PKCS7(128).padder()
    padded_data = padder.update(plaintext) + padder.finalize()
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    encryptor = cipher.encryptor()
    return encryptor.update(padded_data) + encryptor.finalize()


def aes_decrypt(key: bytes, iv: bytes, ciphertext: bytes) -> bytes:
    """AES CBC decrypt and remove PKCS#7 padding."""
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    decryptor = cipher.decryptor()
    decrypted = decryptor.update(ciphertext) + decryptor.finalize()
    num_padding = int(decrypted[-1])
    if 1 <= num_padding <= 16:
        if all(val == num_padding for val in decrypted[-num_padding:]):
            return decrypted[:-num_padding]
    return decrypted


class DecoClient:
    def __init__(self, host: str, password: str):
        self.host = host.rstrip("/")
        self.password = password
        self.stok = None

        # Build base URL (add http:// if not present)
        if not self.host.startswith("http"):
            self.host = f"http://{self.host}"

        self.client = httpx.Client(
            timeout=15.0,
            verify=False,  # Deco uses self-signed certs
            follow_redirects=True,
        )

        # Cryptography / Encrypted API states
        self.encrypted_mode = False
        self.username = ""
        self.cookie = None
        self._aes_key = None
        self._aes_key_bytes = None
        self._aes_iv = None
        self._aes_iv_bytes = None
        self._password_rsa_n = None
        self._password_rsa_e = None
        self._sign_rsa_n = None
        self._sign_rsa_e = None
        self._seq = None

    def _get_headers(self) -> dict:
        """Get headers needed to mimic a browser request (including Referer/Origin for CSRF bypass)."""
        headers = {
            "Content-Type": "application/json",
            "Referer": f"{self.host}/",
            "Origin": self.host,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
        }
        if getattr(self, "cookie", None):
            headers["Cookie"] = f"sysauth={self.cookie}"
        return headers

    def _build_url(self, path: str = "") -> str:
        """Build URL with stok token."""
        token = self.stok or ""
        return f"{self.host}{CGI_PATH}{token}/{path}"

    def _extract_cookie(self, resp):
        cookie_header = resp.headers.get("set-cookie")
        if cookie_header:
            import re
            match = re.search(r"sysauth=([a-f0-9]+)", cookie_header)
            if match:
                self.cookie = match.group(1)

    def _hash_password(self, password: str) -> str:
        """
        Hash the password using MD5 as used by Deco's legacy local admin interface.
        """
        return hashlib.md5(password.encode("utf-8")).hexdigest()

    def _generate_aes_key_and_iv(self):
        """TP-Link requires key and IV to be a 16 digit number (no leading 0s)."""
        min_key = 1000000000000000
        max_key = 9999999999999999
        self._aes_key = secrets.randbelow(max_key - min_key) + min_key
        self._aes_iv = secrets.randbelow(max_key - min_key) + min_key
        self._aes_key_bytes = str(self._aes_key).encode("utf-8")
        self._aes_iv_bytes = str(self._aes_iv).encode("utf-8")

    def _fetch_keys(self):
        url = self._build_url("login?form=keys")
        payload = {"operation": "read"}
        resp = self.client.post(url, json=payload, headers=self._get_headers())
        resp.raise_for_status()
        data = resp.json()
        result = data["result"]
        self.username = result.get("username", "") or "admin"
        keys = result["password"]
        self._password_rsa_n = int(keys[0], 16)
        self._password_rsa_e = int(keys[1], 16)

    def _fetch_auth(self):
        url = self._build_url("login?form=auth")
        payload = {"operation": "read"}
        resp = self.client.post(url, json=payload, headers=self._get_headers())
        resp.raise_for_status()
        data = resp.json()
        auth_result = data["result"]
        auth_key = auth_result["key"]
        self._sign_rsa_n = int(auth_key[0], 16)
        self._sign_rsa_e = int(auth_key[1], 16)
        self._seq = auth_result["seq"]

    def _encode_payload(self, payload: dict) -> str:
        # Encrypt data
        payload_json = json.dumps(payload, separators=(",", ":"))
        data_encrypted = aes_encrypt(self._aes_key_bytes, self._aes_iv_bytes, payload_json.encode("utf-8"))
        data_b64 = base64.b64encode(data_encrypted).decode("utf-8")
        
        # Encrypt sign
        auth_hash = hashlib.md5(f"{self.username}{self.password}".encode("utf-8")).hexdigest()
        seq_with_data_len = self._seq + len(data_b64)
        sign_text = f"k={self._aes_key}&i={self._aes_iv}&h={auth_hash}&s={seq_with_data_len}"
        sign = rsa_encrypt(self._sign_rsa_n, self._sign_rsa_e, sign_text.encode("utf-8"))
        
        return f"sign={sign}&data={urllib.parse.quote_plus(data_b64)}"

    def _decrypt_data(self, data_str: str) -> dict:
        if not data_str:
            return {}
        try:
            data_decoded = base64.b64decode(data_str)
            decrypted = aes_decrypt(self._aes_key_bytes, self._aes_iv_bytes, data_decoded)
            return json.loads(decrypted.decode("utf-8"))
        except Exception as e:
            logger.error(f"Deco decryption error: {e}")
            return {}

    def login(self) -> bool:
        """
        Authenticate with the Deco admin interface.
        Tries encrypted login (new firmware) and falls back to legacy MD5 login.
        """
        logger.info("Attempting Deco login...")
        
        # 1. Try Encrypted Login Handshake
        try:
            self._generate_aes_key_and_iv()
            self._fetch_keys()
            self._fetch_auth()
            
            password_encrypted = rsa_encrypt(self._password_rsa_n, self._password_rsa_e, self.password.encode("utf-8"))
            login_payload = {
                "params": {"password": password_encrypted},
                "operation": "login",
            }
            
            url = self._build_url("login?form=login")
            encoded_body = self._encode_payload(login_payload)
            
            resp = self.client.post(
                url,
                content=encoded_body,
                headers={
                    **self._get_headers(),
                    "Content-Type": "application/json",
                }
            )
            resp.raise_for_status()
            response_json = resp.json()
            
            # Extract and store cookie
            self._extract_cookie(resp)
            
            decrypted_data = self._decrypt_data(response_json.get("data", ""))
            error_code = decrypted_data.get("error_code")
            if error_code is None:
                error_code = decrypted_data.get("errorcode")
            
            if error_code == 0:
                result = decrypted_data.get("result", {})
                stok = result.get("stok")
                if stok:
                    self.stok = stok
                    self.encrypted_mode = True
                    logger.info("Deco encrypted login successful")
                    return True
            
            logger.warning(f"Deco encrypted login failed (error_code={error_code}). Falling back to legacy login.")
            
        except Exception as e:
            logger.warning(f"Deco encrypted login handshake failed ({e}). Falling back to legacy login.")
            
        # 2. Legacy Login (MD5 fallback)
        self.encrypted_mode = False
        url = self._build_url("login?form=login")
        hashed = self._hash_password(self.password)
        payload = {
            "operation": "login",
            "params": {
                "password": hashed,
            },
        }
        
        try:
            resp = self.client.post(
                url,
                json=payload,
                headers=self._get_headers(),
            )
            resp.raise_for_status()
            
            # Extract and store cookie
            self._extract_cookie(resp)
            
            data = resp.json()
            
            stok = None
            if isinstance(data, dict):
                if "result" in data and isinstance(data["result"], dict):
                    stok = data["result"].get("stok")
                elif "data" in data and isinstance(data["data"], dict):
                    stok = data["data"].get("stok")
                elif "stok" in data:
                    stok = data["stok"]

            if stok:
                self.stok = stok
                logger.info("Deco legacy login successful")
                return True
            else:
                error_code = data.get("error_code", "unknown")
                logger.error(f"Deco legacy login failed. Response: {data}")
                raise Exception(f"Login failed (error_code: {error_code}). Check password.")
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Deco login HTTP error: {e}")
            raise Exception(f"Deco login failed: HTTP {e.response.status_code}")
        except httpx.ConnectError as e:
            logger.error(f"Deco connection error: {e}")
            raise Exception(f"Cannot reach Deco at {self.host}. Check the address.")
        except Exception as e:
            if "Login failed" in str(e) or "Cannot reach" in str(e):
                raise
            logger.error(f"Deco login exception: {e}")
            raise Exception(f"Deco login failed: {e}")

    def _request(self, path: str, data: dict = None) -> dict:
        """
        Make an authenticated request to the Deco admin API.
        Auto-retries once on session expiry.
        """
        if not self.stok:
            self.login()

        url = self._build_url(path)
        payload = data or {"operation": "read"}

        try:
            if self.encrypted_mode:
                encoded_body = self._encode_payload(payload)
                resp = self.client.post(
                    url,
                    content=encoded_body,
                    headers={
                        **self._get_headers(),
                        "Content-Type": "application/json",
                    }
                )
            else:
                resp = self.client.post(
                    url,
                    json=payload,
                    headers=self._get_headers(),
                )

            self._extract_cookie(resp)

            # Session expired — retry login
            if resp.status_code in (401, 403):
                logger.warning("Deco session expired, re-authenticating...")
                self.stok = None
                self.login()
                url = self._build_url(path)
                
                if self.encrypted_mode:
                    encoded_body = self._encode_payload(payload)
                    resp = self.client.post(
                        url,
                        content=encoded_body,
                        headers={
                            **self._get_headers(),
                            "Content-Type": "application/json",
                        }
                    )
                else:
                    resp = self.client.post(
                        url,
                        json=payload,
                        headers=self._get_headers(),
                    )
                self._extract_cookie(resp)

            resp.raise_for_status()
            result = resp.json()
            
            if self.encrypted_mode:
                result = self._decrypt_data(result.get("data", ""))

            # Check for error_code in response
            error_code = result.get("error_code", 0)
            if error_code != 0:
                # Token expired error
                if error_code in (-5, -1):
                    logger.warning(f"Deco token error ({error_code}), re-authenticating...")
                    self.stok = None
                    self.login()
                    url = self._build_url(path)
                    
                    if self.encrypted_mode:
                        encoded_body = self._encode_payload(payload)
                        resp = self.client.post(
                            url,
                            content=encoded_body,
                            headers={
                                **self._get_headers(),
                                "Content-Type": "application/json",
                            }
                        )
                    else:
                        resp = self.client.post(
                            url,
                            json=payload,
                            headers=self._get_headers(),
                        )
                    self._extract_cookie(resp)
                    resp.raise_for_status()
                    result = resp.json()
                    if self.encrypted_mode:
                        result = self._decrypt_data(result.get("data", ""))
                else:
                    logger.error(f"Deco API error: {result}")

            return result

        except Exception as e:
            logger.error(f"Deco request error ({path}): {e}")
            return {}

    def get_client_list(self, device_mac: str = "default") -> list:
        """
        Fetch all connected Wi-Fi clients.
        POST /admin/client?form=client_list
        Returns list of dicts with: mac, ip, name, online, wire_type, 
        band, signal_level, up_speed, down_speed, deco_device (node MAC)
        """
        result = self._request(
            "admin/client?form=client_list",
            {"operation": "read", "params": {"device_mac": device_mac}},
        )

        clients = []
        # Parse response — handle multiple firmware formats
        client_data = None
        if isinstance(result, dict):
            # Format: {"result": {"client_list": [...]}}
            if "result" in result and isinstance(result["result"], dict):
                client_data = result["result"].get("client_list", [])
            # Format: {"data": {"client_list": [...]}}  
            elif "data" in result and isinstance(result["data"], dict):
                client_data = result["data"].get("client_list", [])
            # Format: {"client_list": [...]}
            elif "client_list" in result:
                client_data = result["client_list"]

        if isinstance(client_data, list):
            for item in client_data:
                if not isinstance(item, dict):
                    continue
                clients.append({
                    "mac": (item.get("mac", "") or "").upper(),
                    "ip": item.get("ip", ""),
                    "name": decode_deco_name(item.get("name", "")),
                    "online": item.get("online", False),
                    "wire_type": item.get("wire_type", ""),  # "wireless" or "wired"
                    "band": item.get("interface", "") or item.get("band", ""),  # "2.4GHz" / "5GHz"
                    "signal_level": item.get("signal_level", None),  # 0-5 scale or dBm
                    "rssi": item.get("rssi", None),  # Some firmware reports raw RSSI
                    "up_speed": item.get("up_speed", 0),
                    "down_speed": item.get("down_speed", 0),
                    "deco_mac": item.get("access_host", "") or item.get("deco_device", ""),
                    "deco_device": item.get("deco_device", ""),
                })

        logger.info(f"Deco: fetched {len(clients)} clients")
        return clients

    def get_deco_nodes(self) -> list:
        """
        Fetch all Deco mesh nodes (main unit + satellites).
        POST /admin/device?form=device_list
        Returns list of dicts with: mac, name, ip, role, hardware_ver,
        firmware_ver, cpu_usage, mem_usage, client_count
        """
        result = self._request(
            "admin/device?form=device_list",
            {"operation": "read"},
        )

        nodes = []
        node_data = None
        if isinstance(result, dict):
            if "result" in result and isinstance(result["result"], dict):
                node_data = result["result"].get("device_list", [])
            elif "data" in result and isinstance(result["data"], dict):
                node_data = result["data"].get("device_list", [])
            elif "device_list" in result:
                node_data = result["device_list"]

        if isinstance(node_data, list):
            for item in node_data:
                if not isinstance(item, dict):
                    continue
                raw_node_name = item.get("custom_nickname", "") or item.get("nickname", "")
                node_name = decode_deco_name(raw_node_name) or item.get("device_model", "") or "Deco Unit"
                nodes.append({
                    "mac": (item.get("mac", "") or "").upper(),
                    "name": node_name,
                    "ip": item.get("device_ip", "") or item.get("ip", ""),
                    "role": item.get("role", ""),  # "master" / "slave"
                    "hardware_ver": item.get("hardware_ver", ""),
                    "firmware_ver": item.get("software_ver", "") or item.get("firmware_ver", ""),
                    "cpu_usage": item.get("cpu_usage", None),
                    "mem_usage": item.get("mem_usage", None),
                    "client_count": item.get("nand_flash", None),  # Some firmware uses this field
                    "inet_status": item.get("inet_status", ""),
                    "group_status": item.get("group_status", ""),
                })

        logger.info(f"Deco: fetched {len(nodes)} mesh nodes")
        return nodes

    def verify(self) -> bool:
        """Quick login check to validate credentials."""
        self.login()
        # Try a simple read
        nodes = self.get_deco_nodes()
        return True

    def sync(self, force=False):
        """
        Full sync: login → fetch nodes + clients → upsert to DuckDB.
        Updates device attributes and records signal history.
        """
        start_time = time.time()
        logger.info("Deco sync starting...")

        try:
            self.login()

            # Fetch data
            nodes = self.get_deco_nodes()

            # Fetch clients connected to each node separately to resolve correct node association
            clients = []
            for node in nodes:
                node_mac = node.get("mac", "")
                if node_mac:
                    try:
                        node_clients = self.get_client_list(node_mac)
                        for c in node_clients:
                            # Explicitly tag the client with this specific node's MAC address
                            c["deco_mac"] = node_mac.upper()
                            c["deco_device"] = node_mac.upper()
                        clients.extend(node_clients)
                    except Exception as e:
                        logger.warning(f"Deco: failed to fetch client list for node {node.get('name')} ({node_mac}): {e}")

            # Fallback to default list if no clients were fetched from individual nodes
            if not clients:
                try:
                    logger.info("Deco: No clients found via per-node query. Falling back to default list query.")
                    clients = self.get_client_list("default")
                except Exception as e:
                    logger.warning(f"Deco: default client list fallback failed: {e}")

            # Build node MAC → name mapping for enrichment
            node_map = {}
            node_by_index = {}
            for idx, node in enumerate(nodes):
                mac = node.get("mac", "").lower().replace("-", ":")
                if mac:
                    node_map[mac] = node
                node_by_index[str(idx)] = node

            conn = get_connection()
            try:
                updated_count = 0
                signal_records = 0
                node_mac_to_device_id = {}

                # 1. Process Deco Nodes themselves (enrich as devices)
                for node in nodes:
                    mac = node.get("mac", "").lower().replace("-", ":")
                    if not mac:
                        continue

                    row = conn.execute(
                        "SELECT id, attributes, name, ip FROM devices WHERE LOWER(mac) = ?",
                        [mac],
                    ).fetchone()

                    if not row and node.get("ip"):
                        row = conn.execute(
                            "SELECT id, attributes, name, ip FROM devices WHERE ip = ? AND (mac IS NULL OR mac = '')",
                            [node.get("ip")],
                        ).fetchone()
                        if row:
                            device_id = row[0]
                            conn.execute(
                                "UPDATE devices SET mac = ? WHERE id = ?",
                                [mac, device_id]
                            )

                    if not row:
                        continue

                    device_id = row[0]
                    node_mac_to_device_id[mac] = device_id

                    # Prepare attributes
                    existing_attrs = {
                        "deco_role": node.get("role", ""),
                        "deco_hw_ver": node.get("hardware_ver", ""),
                        "deco_fw_ver": node.get("firmware_ver", ""),
                        "deco_node_name": node.get("name", ""),
                        "last_sync": "deco",
                        "connection_type": "wired" if node.get("role") == "master" else "wireless"
                    }
                    if node.get("cpu_usage") is not None:
                        existing_attrs["deco_cpu_usage"] = node["cpu_usage"]
                    if node.get("mem_usage") is not None:
                        existing_attrs["deco_mem_usage"] = node["mem_usage"]

                    device_id = row[0]
                    current_ip = row[3]
                    new_ip = node.get("ip", "")

                    db_attrs = {}
                    if row[1]:
                        try:
                            db_attrs = json.loads(row[1])
                        except:
                            pass
                    db_attrs.update(existing_attrs)

                    if new_ip and new_ip != current_ip:
                        conn.execute(
                            "UPDATE devices SET attributes = ?, last_seen = ?, status = 'online', ip = ? WHERE id = ?",
                            [json.dumps(db_attrs), utc_now(), new_ip, device_id],
                        )
                    else:
                        conn.execute(
                            "UPDATE devices SET attributes = ?, last_seen = ?, status = 'online' WHERE id = ?",
                            [json.dumps(db_attrs), utc_now(), device_id],
                        )
                    updated_count += 1

                # 2. Process Connected Clients
                for client in clients:
                    mac = client.get("mac", "").lower().replace("-", ":")
                    if not mac or mac == "00:00:00:00:00:00":
                        continue

                    row = conn.execute(
                        "SELECT id, attributes, name, ip FROM devices WHERE LOWER(mac) = ?",
                        [mac],
                    ).fetchone()

                    if not row and client.get("ip"):
                        row = conn.execute(
                            "SELECT id, attributes, name, ip FROM devices WHERE ip = ? AND (mac IS NULL OR mac = '')",
                            [client.get("ip")],
                        ).fetchone()
                        if row:
                            device_id = row[0]
                            conn.execute(
                                "UPDATE devices SET mac = ? WHERE id = ?",
                                [mac, device_id]
                            )

                    if not row:
                        continue

                    # Determine connection parameters
                    existing_attrs = {}
                    wire_type = client.get("wire_type", "").lower()
                    if "wire" in wire_type and "wireless" not in wire_type:
                        existing_attrs["connection_type"] = "wired"
                    else:
                        existing_attrs["connection_type"] = "wireless"

                    band = client.get("band", "")
                    if band:
                        if "2.4" in str(band) or "2g" in str(band).lower():
                            existing_attrs["wlan_band"] = "2.4GHz"
                        elif "5" in str(band) or "5g" in str(band).lower():
                            existing_attrs["wlan_band"] = "5GHz"
                        else:
                            existing_attrs["wlan_band"] = str(band)

                    rssi = client.get("rssi") or client.get("signal_level")
                    if rssi is not None:
                        try:
                            rssi_int = int(rssi)
                            existing_attrs["wlan_rssi"] = rssi_int
                        except (ValueError, TypeError):
                            pass

                    deco_mac = (client.get("deco_mac", "") or "").lower().replace("-", ":")
                    deco_node_info = {}
                    if deco_mac in node_map:
                        deco_node_info = node_map[deco_mac]
                    elif deco_mac.isdigit() and deco_mac in node_by_index:
                        deco_node_info = node_by_index[deco_mac]

                    deco_node_name = deco_node_info.get("name", "")
                    if deco_node_name:
                        existing_attrs["deco_node"] = deco_node_name
                        existing_attrs["mesh_node"] = deco_node_name

                    existing_attrs["last_sync"] = "deco"

                    device_id = row[0]
                    current_ip = row[3]
                    new_ip = client.get("ip", "")
                    if new_ip and new_ip != current_ip:
                        conn.execute(
                            "UPDATE devices SET ip = ? WHERE id = ?",
                            [new_ip, device_id]
                        )
                    
                    # Update parent_id based on connected Deco Node
                    resolved_node_mac = deco_mac
                    if deco_mac.isdigit() and deco_mac in node_by_index:
                        resolved_node_mac = node_by_index[deco_mac].get("mac", "").lower().replace("-", ":")
                    
                    parent_device_id = node_mac_to_device_id.get(resolved_node_mac)
                    conn.execute(
                        "UPDATE devices SET parent_id = ? WHERE id = ?",
                        [parent_device_id, device_id]
                    )
                    
                    conn.execute(
                        """
                        INSERT OR REPLACE INTO device_discovery_sources (device_id, source, last_seen, status, attributes)
                        VALUES (?, 'deco', ?, 'online', ?)
                        """,
                        [device_id, utc_now(), json.dumps(existing_attrs)]
                    )
                    from app.services.devices import recalculate_device_status
                    recalculate_device_status(conn, device_id)
                    updated_count += 1

                    # 3. Record signal history (wifi_signal_history)
                    if rssi is not None:
                        try:
                            hist_id = str(uuid.uuid4())
                            conn.execute(
                                """INSERT INTO wifi_signal_history 
                                   (id, device_id, rssi, band, mesh_node, source) 
                                   VALUES (?, ?, ?, ?, ?, 'deco')""",
                                [
                                    hist_id,
                                    device_id,
                                    int(rssi),
                                    existing_attrs.get("wlan_band", ""),
                                    deco_node_name,
                                ],
                            )
                            signal_records += 1
                        except Exception as e:
                            logger.error(f"Failed to insert signal history for {mac}: {e}")

                conn.commit()
                logger.info(
                    f"Deco sync complete: {updated_count} devices updated, "
                    f"{signal_records} signal records, {len(nodes)} nodes"
                )

            finally:
                conn.close()

            duration = int((time.time() - start_time) * 1000)

            log_task_event(
                task_type="deco_sync",
                event_type="completed",
                message=f"Deco sync completed. {updated_count} devices updated, {len(nodes)} nodes found.",
                target="deco",
                duration_ms=duration,
                details={
                    "nodes_count": len(nodes),
                    "clients_count": len(clients),
                    "updated_devices": updated_count,
                    "signal_records": signal_records,
                },
            )

            return True

        except Exception as e:
            logger.error(f"Deco sync failed: {e}", exc_info=True)

            duration = int((time.time() - start_time) * 1000)
            log_task_event(
                task_type="deco_sync",
                event_type="failed",
                message=f"Deco sync failed: {str(e)}",
                target="deco",
                duration_ms=duration,
                level="ERROR",
            )

            raise
