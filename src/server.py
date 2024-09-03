import logging
from websockets import WebSocketServerProtocol, serve
import json
import asyncio
from typing import Callable, Dict, Any
from behavior_tree import *
from jwt import InvalidTokenError

class Server(ABC):
    @abstractmethod
    async def run(self) -> xNodeResult:
        pass
    @abstractmethod
    async def handler(self, websocket: WebSocketServerProtocol) -> xNodeResult:
        pass

class Command(ABC):
    @abstractmethod
    async def execute(self, server: Server, request: Dict[str, Any]) -> Dict[str, Any]:
        pass
    

class xNodeServer(Server):
    
    def __init__(self, host: str = "localhost", port: int = 8765, loop: asyncio.AbstractEventLoop = None) -> None:
        self.host = host
        self.port = port
        self.behavior_trees: Dict[str, BehaviorTree] = {}
        self.actions: Dict[str, Callable] = {}
        self.conditions: Dict[str, Callable] = {}
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger()
        self.loop = loop or asyncio.get_event_loop()

    def register_action(self, name: str, action: Callable[[], Union[bool, Awaitable[bool]]]) -> xNodeResult:
        if name in self.actions:
            self.logger.error(f"Action '{name}' is already registered. It will be overridden.")
            return xNodeResult(xNodeStatus.Failure)
        self.actions[name] = action
        self.logger.info(f"Action '{name}' registered.")
        return xNodeResult(xNodeStatus.Success)

    def register_condition(self, name: str, condition: Callable[[], Union[bool, Awaitable[bool]]]) -> xNodeResult:
        if name in self.conditions:
            self.logger.error(f"Condition '{name}' is already registered. It will be overridden.")
            return xNodeResult(xNodeStatus.Failure)
        self.conditions[name] = condition
        self.logger.info(f"Condition '{name}' registered.")
        return xNodeResult(xNodeStatus.Success)

    async def handler(self, websocket: WebSocketServerProtocol) -> xNodeResult:
        async for message in websocket:
            try:
                request = json.loads(message)
                command = request.get("command")
                self.logger.info(f"Received command: {command}")
                response = await self.process_command(command, request)
            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to decode JSON: {e}")
                response = {"status": "error", "message": "Invalid JSON format."}
            except Exception as e:
                self.logger.error(f"Error processing command: {e}")
                response = {"status": "error", "message": str(e)}

            await websocket.send(json.dumps(response))
            self.logger.info(f"Sent response: {response}")
            return xNodeResult(xNodeStatus.Success)

    async def process_command(self, command: str, request: Dict[str, Any]) -> Dict[str, Any]:
        if command == "create_tree":
            return await self._create_tree(request)
        elif command == "run_tree":
            return await self._run_tree(request)
        elif command == "get_actions":
            return self._get_actions()
        elif command == "get_conditions":
            return self._get_conditions()
        elif command == "get_tree":
            return self._get_tree(request)
        else:
            return {"status": "error", "message": f"Unknown command: {command}"}

    async def _create_tree(self, request: Dict[str, Any]) -> Dict[str, Any]:
        tree_id = request.get("tree_id")
        tree_structure = request.get("tree_structure")
        if tree_id and tree_structure:
            tree = self._create_tree_from_dict(tree_structure)
            self.behavior_trees[tree_id] = tree
            self.logger.info(f"Tree {tree_id} created.")
            return {"status": "success", "message": f"Tree {tree_id} created."}
        else:
            self.logger.warning("Invalid tree creation request.")
            return {"status": "error", "message": "Invalid tree creation request."}

    async def _run_tree(self, request: Dict[str, Any]) -> Dict[str, Any]:
        tree_id = request.get("tree_id")
        if tree_id in self.behavior_trees:
            tree = self.behavior_trees[tree_id]
            await tree.run()
            self.logger.info(f"Tree {tree_id} executed.")
            return {"status": "success", "message": f"Tree {tree_id} executed."}
        else:
            self.logger.warning(f"Tree {tree_id} not found.")
            return {"status": "error", "message": f"Tree {tree_id} not found."}

    def _get_actions(self) -> Dict[str, Any]:
        return {"actions": list(self.actions.keys())}

    def _get_conditions(self) -> Dict[str, Any]:
        return {"conditions": list(self.conditions.keys())}

    def _get_tree(self, request: Dict[str, Any]) -> Dict[str, Any]:
        tree_id = request.get("tree_id")
        if tree_id in self.behavior_trees:
            tree = self.behavior_trees[tree_id]
            return {"tree": tree.to_dict()}
        else:
            self.logger.warning(f"Tree {tree_id} not found.")
            return {"status": "error", "message": f"Tree {tree_id} not found."}

    def _create_tree_from_dict(self, tree_dict: Dict[str, Any]) -> BehaviorTree:
        node_type = tree_dict.get('type')
        if node_type == 'ActionNode':
            return self._create_action_node(tree_dict)
        elif node_type == 'ConditionNode':
            return self._create_condition_node(tree_dict)
        elif node_type in {'SequenceNode', 'SelectorNode', 'ParallelNode'}:
            return self._create_composite_node(tree_dict, node_type)
        elif node_type == 'InvertDecorator':
            return self._create_invert_decorator(tree_dict)
        else:
            self.logger.error(f"Unknown node type: {node_type}")
            raise ValueError(f"Unknown node type: {node_type}")

    def _create_action_node(self, tree_dict: Dict[str, Any]) -> BehaviorTree:
        action_name = tree_dict.get('action')
        action = self.actions.get(action_name)
        if action is None:
            raise ValueError(f"Action '{action_name}' not found.")
        repeat = tree_dict.get('repeat', False)
        repeat_count = tree_dict.get('repeat_count', 1)
        execute_once = tree_dict.get('execute_once', False)
        node = ActionNode(action, repeat, repeat_count, execute_once)
        tree = BehaviorTree()
        tree.update(node)
        return tree

    def _create_condition_node(self, tree_dict: Dict[str, Any]) -> BehaviorTree:
        condition_name = tree_dict.get('condition')
        condition = self.conditions.get(condition_name)
        if condition is None:
            raise ValueError(f"Condition '{condition_name}' not found.")
        node = ConditionNode(condition)
        tree = BehaviorTree()
        tree.update(node)
        return tree

    def _create_composite_node(self, tree_dict: Dict[str, Any], node_type: str) -> BehaviorTree:
        children = [self._create_tree_from_dict(child_dict) for child_dict in tree_dict.get('children', [])]
        if node_type == 'SequenceNode':
            node = SequenceNode(children)
        elif node_type == 'SelectorNode':
            node = SelectorNode(children)
        elif node_type == 'ParallelNode':
            success_threshold = tree_dict.get('success_threshold', len(children))
            node = ParallelNode(children, success_threshold)
        tree = BehaviorTree()
        tree.update(node)
        return tree

    def _create_invert_decorator(self, tree_dict: Dict[str, Any]) -> BehaviorTree:
        child_dict = tree_dict.get('child')
        child = self._create_tree_from_dict(child_dict)
        node = InvertDecorator(child)
        tree = BehaviorTree()
        tree.update(node)
        return tree

    async def run(self) -> xNodeResult:
        server = serve(self.handler, self.host, self.port)
        await server
        self.logger.info(f"Server started on {self.host}:{self.port}")
        await asyncio.Future()
        return xNodeResult(xNodeStatus.Success)
