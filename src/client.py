import asyncio
import websockets
import json
from typing import Any, Dict, Optional, Type
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("xNodeClient")

class Command:
    def __init__(self, name: str, **kwargs: Any) -> None:
        self.name = name
        self.kwargs = kwargs

    def to_dict(self) -> Dict[str, Any]:
        command = {"command": self.name}
        command.update(self.kwargs)
        return command

class CreateTreeCommand(Command):
    def __init__(self, tree_id: str, tree_structure: Dict[str, Any]) -> None:
        super().__init__("create_tree", tree_id=tree_id, tree_structure=tree_structure)

class RunTreeCommand(Command):
    def __init__(self, tree_id: str) -> None:
        super().__init__("run_tree", tree_id=tree_id)

class GetActionsCommand(Command):
    def __init__(self) -> None:
        super().__init__("get_actions")

class GetConditionsCommand(Command):
    def __init__(self) -> None:
        super().__init__("get_conditions")

class GetTreeCommand(Command):
    def __init__(self, tree_id: str) -> None:
        super().__init__("get_tree", tree_id=tree_id)

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
    await client.send(GetActionsCommand())
    await client.close()

asyncio.run(main())
