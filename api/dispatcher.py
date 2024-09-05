import asyncio
import json
import websockets
from typing import Awaitable, Callable, Dict, Any, Union
import sys
from command import RegisterAction, RegisterCondition, xNodeCommand
from dp_store import xNodeDpStore

class xNodeDispatcher:
    def __init__(self, server_uri: str) -> None:
        self.server_uri = server_uri
        self.__store = xNodeDpStore()

    async def __register(self, name: str, func: Callable[[], Union[bool, Awaitable[bool]]], command: xNodeCommand) -> Dict[str, Any]:
        
        async with websockets.connect(self.server_uri) as websocket:
            message = json.dumps({
                'command': command,
                'name': name
            })
            await websocket.send(message)
            response = await websocket.recv()
            _ = json.loads(response)

            return command.execute(self.__store, name, func)
        
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
        return await self.__register(name, action, RegisterAction())

    async def register_condition(self, name: str, condition: Callable[[], Union[bool, Awaitable[bool]]]) -> Dict[str, Any]:
        return await self.__register(name, condition, RegisterCondition())

    async def invoke_function(self, name: str) -> Union[bool, Awaitable[bool]]:
        if name in self.__store.actions:
            result = await self.__store.actions[name]()
            return result
        elif name in self.__store.conditions:
            result = await self.__store.conditions[name]()
            return result
        else:
            raise ValueError(f"Function {name} not registered")

    async def start(self):
        async with websockets.connect(self.server_uri) as websocket:
            while True:
                message = await websocket.recv()
                request = json.loads(message)
                command = request.get('command')
                if command == "invoke_func":
                    name = request.get('name')
                    if name in self.actions:
                        result = await self.invoke_function(name)
                        response = json.dumps({'result': result})
                        await websocket.send(response)
                    else:
                        error_response = json.dumps({'error': f"Function '{name}' not registered"})
                        await websocket.send(error_response)
                        

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
