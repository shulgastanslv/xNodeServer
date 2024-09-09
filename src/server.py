import logging
from websockets import ConnectionClosedError, ConnectionClosedOK, WebSocketServerProtocol, connect, serve
import json
import asyncio
from typing import Callable, Dict, Any
from src.behavior_tree import *
from src.handlers.abstractions.command_handler import CommandHandler
from src.handlers.actions.register_action import RegisterActionCommandHandler
from src.routes import Routes

class xNodeServer:
    
    def __init__(self, host: str = "localhost", port: int = 8765) -> None:
        self.host = host
        self.port = port
        self.users: List[WebSocketServerProtocol] = []
        self.actions: Dict[str, Callable] = {}
        self.conditions: Dict[str, Callable] = {}
    
    async def handler(self, websocket: WebSocketServerProtocol) -> xNodeResult:
        self.users.append(websocket)
        try:
            async for message in websocket:
                try:
                    request = json.loads(message)
                    command = request.get("command")
                    filtered_request = {k: v for k, v in request.items() if k != "command"}
                    res = self.__filter(filtered_request)
                    if res:
                        response = await res.handler(request)
                    else:
                        response = xNodeResult(xNodeStatus.Failure, False)
                except json.JSONDecodeError as error:
                    response = xNodeResult(xNodeStatus.Failure, False, error)
                except Exception as error:
                    response = xNodeResult(xNodeStatus.Failure, False, str(error))
                await websocket.send(json.dumps(response.__dict__))
        except (ConnectionClosedOK, ConnectionClosedError) as error:
            print(error)
        finally:
            if websocket in self.users:
                self.users.remove(websocket)
        return xNodeResult(xNodeStatus.Success)

    def __filter(self, command: str) -> CommandHandler:
        if command == Routes.RegisterAction:
            return RegisterActionCommandHandler(self.actions)
        elif command == Routes.RegisterCondition:
            pass
        
    async def run(self) -> None:
        async def handle_connection(websocket: WebSocketServerProtocol) -> None:
            await self.handler(websocket)
        async with serve(handle_connection, self.host, self.port):
            await asyncio.Future()
