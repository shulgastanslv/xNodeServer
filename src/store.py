from typing import Dict, List

from websockets import WebSocketServerProtocol

class xNodeStore:
    def __init__(self) -> None:
        self.actions: Dict[str, str] = {}
        self.conditions: Dict[str, str] = {}
        self.active_connections: List[WebSocketServerProtocol] = []