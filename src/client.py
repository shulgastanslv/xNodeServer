import asyncio
import websockets
import json
from typing import Any, Dict, Optional, Type
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

class Command:
    def __init__(self, command_name: str, **kwargs: Any) -> None:
        self.command_name = command_name
        self.kwargs = kwargs

    def to_dict(self) -> Dict[str, Any]:
        command = {"command": self.command_name}
        command.update(self.kwargs)
        return command

class RegisterAction(Command):
    def __init__(self, action_id: str, name_action : str) -> None:
        super().__init__("register_action", id=action_id, name=name_action)

class xNodeClient:
    def __init__(self, host: str = "localhost", port: int = 8765) -> None:
        self.uri = f"ws://{host}:{port}"
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        
    async def connect(self) -> None:
        self.websocket = await websockets.connect(self.uri)
        logger.info("Connected to the WebSocket server.")

    async def send(self, command: Command) -> Dict[str, Any]:
        if not self.websocket:
            logger.error("WebSocket connection is not established. Call connect() first.")
            raise ConnectionError("WebSocket connection is not established. Call connect() first.")
        
        message = command.to_dict()
        await self.websocket.send(json.dumps(message))
        logger.info(f"Sent: {json.dumps(message)}")

        response = await self.websocket.recv()
        logger.info(f"Received: {response}")

        return json.loads(response)

    async def close(self) -> None:
        if self.websocket:
            await self.websocket.close()
            logger.info("Disconnected from the WebSocket server.")

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()


async def main():
    client = xNodeClient()
    await client.connect()
    await client.send(RegisterAction('1', 'test'))
    await client.close()

asyncio.run(main())
