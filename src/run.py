import asyncio
from logging.config import dictConfig
from behavior_tree import SequenceNode
from server import xNodeServer

async def main():
    server = xNodeServer()
    await server.run()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("The xNodeServer is turned off!")