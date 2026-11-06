import json
import asyncio
from typing import Dict, List, Any
from fastapi import WebSocket
from app.core.logging import logger

class WebSocketManager:
    """
    Manages active WebSocket connections for real-time video generation progress streaming.
    """
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, job_id: str, websocket: WebSocket):
        await websocket.accept()
        if job_id not in self.active_connections:
            self.active_connections[job_id] = []
        self.active_connections[job_id].append(websocket)
        logger.info(f"WebSocket client connected to job stream {job_id}")

    def disconnect(self, job_id: str, websocket: WebSocket):
        if job_id in self.active_connections:
            if websocket in self.active_connections[job_id]:
                self.active_connections[job_id].remove(websocket)
            if not self.active_connections[job_id]:
                del self.active_connections[job_id]
        logger.info(f"WebSocket client disconnected from job stream {job_id}")

    async def send_job_update(self, job_id: str, data: Dict[str, Any]):
        if job_id in self.active_connections:
            payload = json.dumps(data)
            dead_sockets = []
            for connection in self.active_connections[job_id]:
                try:
                    await connection.send_text(payload)
                except Exception as e:
                    logger.warning(f"Error sending ws update for {job_id}: {e}")
                    dead_sockets.append(connection)
            for dead in dead_sockets:
                self.disconnect(job_id, dead)

    def broadcast_sync(self, job_id: str, data: Dict[str, Any]):
        """Safe thread-safe synchronous bridge for background worker threads."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.run_coroutine_threadsafe(self.send_job_update(job_id, data), loop)
        except Exception:
            pass

ws_manager = WebSocketManager()

