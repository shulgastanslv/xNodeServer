import asyncio
import json
import websockets
import logging
from typing import Awaitable, Callable, Dict, Any, Union

class xNodeDispatcher:
    def __init__(self, server_uri: str) -> None:
        self.server_uri = server_uri
        self.actions: Dict[str, Callable[[], Union[bool, Awaitable[bool]]]] = {}
        self.conditions: Dict[str, Callable[[], Union[bool, Awaitable[bool]]]] = {}
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    async def _register_function(self, name: str, func: Callable[[], Union[bool, Awaitable[bool]]], is_action: bool) -> Dict[str, Any]:
        async with websockets.connect(self.server_uri) as websocket:
            command = 'register_action' if is_action else 'register_condition'
            message = json.dumps({
                'command': command,
                'name': name
            })
            self.logger.info(f"Sending registration request: {message}")
            await websocket.send(message)
            response = await websocket.recv()
            result = json.loads(response)
            self.logger.info(f"Received registration response: {result}")

            if is_action:
                self.actions[name] = func
                self.logger.info(f"Action '{name}' registered successfully.")
            else:
                self.conditions[name] = func
                self.logger.info(f"Condition '{name}' registered successfully.")

            return result

    def action(self) -> Callable[[Callable[[], Union[bool, Awaitable[bool]]]], Callable[[], Union[bool, Awaitable[bool]]]]:
        def decorator(func: Callable[[], Union[bool, Awaitable[bool]]]) -> Callable[[], Union[bool, Awaitable[bool]]]:
            func_name = func.__name__
            asyncio.create_task(self.register_action(func_name, func))
            return func
        return decorator

    def condition(self) -> Callable[[Callable[[], Union[bool, Awaitable[bool]]]], Callable[[], Union[bool, Awaitable[bool]]]]:
        def decorator(func: Callable[[], Union[bool, Awaitable[bool]]]) -> Callable[[], Union[bool, Awaitable[bool]]]:
            func_name = func.__name__
            asyncio.create_task(self.register_condition(func_name, func))
            return func
        return decorator

    async def register_action(self, name: str, action: Callable[[], Union[bool, Awaitable[bool]]]) -> Dict[str, Any]:
        self.logger.info(f"Registering action: {name}")
        return await self._register_function(name, action, is_action=True)

    async def register_condition(self, name: str, condition: Callable[[], Union[bool, Awaitable[bool]]]) -> Dict[str, Any]:
        self.logger.info(f"Registering condition: {name}")
        return await self._register_function(name, condition, is_action=False)

    async def invoke_function(self, name: str) -> Union[bool, Awaitable[bool]]:
        self.logger.info(f"Invoking function: {name}")
        if name in self.actions:
            result = await self.actions[name]()
            self.logger.info(f"Action '{name}' executed with result: {result}")
            return result
        elif name in self.conditions:
            result = await self.conditions[name]()
            self.logger.info(f"Condition '{name}' evaluated with result: {result}")
            return result
        else:
            self.logger.error(f"Function '{name}' not registered")
            raise ValueError(f"Function {name} not registered")

    async def start(self):
        async with websockets.connect(self.server_uri) as websocket:
            while True:
                message = await websocket.recv()
                request = json.loads(message)
                self.logger.info(f"Received invocation request: {request}")
                command = request.get('command')
                if command == 'invoke_func':
                    name = request.get('name')
                    if name in self.actions:
                        result = await self.invoke_function(name)
                        response = json.dumps({'result': result})
                        await websocket.send(response)
                        self.logger.info(f"Executed '{name}' with result: {result}")
                    else:
                        error_response = json.dumps({'error': f"Function '{name}' not registered"})
                        await websocket.send(error_response)
                        self.logger.error(f"Function '{name}' not found")

async def main():
    server_uri = 'ws://localhost:8765'
    dispatcher = xNodeDispatcher(server_uri)

    @dispatcher.action()
    async def hello() -> bool:
        print("Hello World!")
        return True

    await dispatcher.start()

if __name__ == '__main__':
    asyncio.run(main())
