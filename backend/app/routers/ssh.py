from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Query, status
import asyncio
import paramiko
import logging
import json
from typing import Optional
from jose import jwt, JWTError
from app.core.auth import settings

router = APIRouter()
logger = logging.getLogger(__name__)

class SSHSession:
    def __init__(self, host: str, port: int = 22, username: str = None, password: str = None):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.shell = None

    async def connect(self):
        try:
            await asyncio.to_thread(
                self.client.connect,
                hostname=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                timeout=10,
                allow_agent=False,
                look_for_keys=False
            )
            self.shell = self.client.invoke_shell(term='xterm')
            self.shell.setblocking(0)
            return True
        except Exception as e:
            logger.error(f"SSH Connection failed: {e}")
            return False

    async def read(self):
        # We don't really need to_thread for a non-blocking recv if it's already ready
        # But we'll keep it for safety in case of OS-level blocking
        if self.shell and self.shell.recv_ready():
            try:
                return await asyncio.to_thread(self.shell.recv, 1024)
            except Exception as e:
                logger.error(f"SSH Read Error: {e}")
                raise e
        return None

    async def write(self, data: str):
        if self.shell:
            await asyncio.to_thread(self.shell.send, data)

    def close(self):
        self.client.close()

async def get_token_from_query(token: str = Query(None)):
    if token is None:
        return None
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload.get("sub")
    except JWTError:
        return None

@router.websocket("/ws/{ip}")
async def ssh_websocket_endpoint(websocket: WebSocket, ip: str, token: str = Query(None)):
    logger.info(f"SSH WebSocket connection attempt for {ip}")
    
    # Verify token
    username_jwt = await get_token_from_query(token)
    if not username_jwt:
        logger.warning("SSH WebSocket connection rejected: Invalid or missing token")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await websocket.accept()
    session: Optional[SSHSession] = None
    
    try:
        # 1. Wait for credentials
        auth_data = await websocket.receive_json()
        username = auth_data.get("username")
        password = auth_data.get("password")
        port = auth_data.get("port", 22)

        session = SSHSession(ip, port, username, password)
        logger.info(f"Connecting to SSH {ip}:{port}...")
        if await session.connect():
            logger.info("SSH Connected Successfully")
            await websocket.send_text("\r\n*** Connected to " + ip + " ***\r\n")
        else:
            logger.warning("SSH Connection Failed")
            await websocket.send_text("\r\n*** Connection Failed ***\r\n")
            await websocket.close()
            return

        # 2. Loop for bi-directional communication
        # We need a way to run the read loop concurrently with the receive loop
        
        async def read_from_ssh():
            while True:
                try:
                    data = await session.read()
                    if data:
                        await websocket.send_bytes(data)
                    else:
                        # 0.05s = 20Hz polling. Much better for CPU.
                        await asyncio.sleep(0.05)
                except Exception as e:
                    logger.debug(f"SSH Read loop ended: {e}")
                    break

        # Start the reader task
        reader_task = asyncio.create_task(read_from_ssh())

        # Main loop: read from websocket (user input) -> write to SSH
        while True:
            data = await websocket.receive_text()
            await session.write(data)

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"SSH WebSocket Error: {e}")
    finally:
        if session:
            session.close()
