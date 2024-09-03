import asyncio
from logging.config import dictConfig
from behavior_tree import SequenceNode
from server import xNodeServer

async def main():
    server = xNodeServer()
    server.register_action('helo_world!', lambda: print("HelloWorld"))
    server.register_action('helo_world!', lambda: print("HelloWorld"))
    await server.run()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("The xNodeServer is turned off!")