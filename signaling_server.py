import asyncio
import json
import logging
from typing import Dict, Set
from websockets.server import serve
from websockets import WebSocketServerProtocol

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SignalingServer:
    def __init__(self, host: str = "0.0.0.0", port: int = 8765):
        self.host = host
        self.port = port
        self.clients: Dict[str, WebSocketServerProtocol] = {}
        self.rooms: Dict[str, Set[str]] = {}

    async def handle_connection(self, websocket: WebSocketServerProtocol):
        client_id = None
        room_id = None

        try:
            async for message in websocket:
                data = json.loads(message)
                message_type = data.get("type")

                if message_type == "join":
                    client_id = data.get("client_id")
                    room_id = data.get("room_id", "default")
                    await self.handle_join(websocket, client_id, room_id)

                elif message_type == "offer":
                    await self.handle_offer(client_id, room_id, data)

                elif message_type == "answer":
                    await self.handle_answer(client_id, room_id, data)

                elif message_type == "ice_candidate":
                    await self.handle_ice_candidate(client_id, room_id, data)

                elif message_type == "leave":
                    await self.handle_leave(client_id, room_id)

        except Exception as e:
            logger.error(f"Error handling connection: {e}")
        finally:
            if client_id and room_id:
                await self.handle_leave(client_id, room_id)

    async def handle_join(self, websocket: WebSocketServerProtocol, client_id: str, room_id: str):
        self.clients[client_id] = websocket

        if room_id not in self.rooms:
            self.rooms[room_id] = set()

        self.rooms[room_id].add(client_id)
        logger.info(f"Client {client_id} joined room {room_id}")

        await self.broadcast_to_room(room_id, {
            "type": "user_joined",
            "client_id": client_id
        }, exclude=client_id)

        existing_clients = list(self.rooms[room_id] - {client_id})
        await websocket.send(json.dumps({
            "type": "room_info",
            "room_id": room_id,
            "existing_clients": existing_clients
        }))

    async def handle_offer(self, sender_id: str, room_id: str, data: dict):
        target_id = data.get("target_id")
        if target_id and target_id in self.clients:
            await self.clients[target_id].send(json.dumps({
                "type": "offer",
                "sender_id": sender_id,
                "sdp": data.get("sdp")
            }))

    async def handle_answer(self, sender_id: str, room_id: str, data: dict):
        target_id = data.get("target_id")
        if target_id and target_id in self.clients:
            await self.clients[target_id].send(json.dumps({
                "type": "answer",
                "sender_id": sender_id,
                "sdp": data.get("sdp")
            }))

    async def handle_ice_candidate(self, sender_id: str, room_id: str, data: dict):
        target_id = data.get("target_id")
        if target_id and target_id in self.clients:
            await self.clients[target_id].send(json.dumps({
                "type": "ice_candidate",
                "sender_id": sender_id,
                "candidate": data.get("candidate")
            }))

    async def handle_leave(self, client_id: str, room_id: str):
        if client_id in self.clients:
            del self.clients[client_id]

        if room_id in self.rooms and client_id in self.rooms[room_id]:
            self.rooms[room_id].remove(client_id)
            await self.broadcast_to_room(room_id, {
                "type": "user_left",
                "client_id": client_id
            })

            if not self.rooms[room_id]:
                del self.rooms[room_id]

        logger.info(f"Client {client_id} left room {room_id}")

    async def broadcast_to_room(self, room_id: str, message: dict, exclude: str = None):
        if room_id not in self.rooms:
            return

        message_str = json.dumps(message)
        for client_id in self.rooms[room_id]:
            if exclude and client_id == exclude:
                continue
            if client_id in self.clients:
                try:
                    await self.clients[client_id].send(message_str)
                except Exception as e:
                    logger.error(f"Error sending to client {client_id}: {e}")

    async def start(self):
        logger.info(f"Starting signaling server on {self.host}:{self.port}")
        async with serve(self.handle_connection, self.host, self.port):
            await asyncio.Future()


async def main():
    server = SignalingServer()
    await server.start()


if __name__ == "__main__":
    asyncio.run(main())
