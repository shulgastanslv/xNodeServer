import asyncio
import http
import json
from typing import Callable, Dict, List
from mediatr import Mediator
import websockets
from src.handlers.actions.register_action import RegisterActionCommandHandler
from src.requests.actions.register_action import RegisterActionRequest
from src.router import Router

users: List[websockets.WebSocketServerProtocol] = []
actions: Dict[str, Callable] = {}
conditions: Dict[str, Callable] = {}
router = Router()
mediator = Mediator()
mediator.register_handler(RegisterActionCommandHandler)
  
@router.route("/register_action")
async def register_action(ws, path):
    request = RegisterActionRequest(**json.loads(await ws.recv()))
    result = await mediator.send_async(request)
    await ws.send(str(result))

async def main():
    server = await router.serve('localhost', 1337)
    await server.wait_closed()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass