import asyncio
import threading
from collections import defaultdict
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self.rooms = defaultdict(set)
        self.loops = {}
        self.lock = threading.Lock()

    async def connect(self, websocket: WebSocket, room: str):
        await websocket.accept() if websocket.client_state.name != "CONNECTED" else None
        with self.lock:
            self.rooms[room].add(websocket)
            self.loops[websocket] = asyncio.get_running_loop()

    def disconnect(self, websocket: WebSocket, room: str):
        with self.lock:
            self.rooms[room].discard(websocket)
            if not self.rooms[room]:
                self.rooms.pop(room, None)
            if not any(websocket in clients for clients in self.rooms.values()):
                self.loops.pop(websocket, None)

    async def broadcast(self, room: str, message: dict):
        with self.lock:
            clients = list(self.rooms.get(room, set()))
        for ws in clients:
            try:
                await ws.send_json(message)
            except Exception:
                self.disconnect(ws, room)

    def broadcast_sync(self, room: str, message: dict):
        with self.lock:
            clients = list(self.rooms.get(room, set()))
            loops = {ws: self.loops.get(ws) for ws in clients}
        for ws, loop in loops.items():
            if loop and loop.is_running():
                asyncio.run_coroutine_threadsafe(ws.send_json(message), loop)

manager = ConnectionManager()
