import asyncio
from common.config import Config
from src.server import xNodeServer

async def main():
    server = xNodeServer()
    await server.run()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass