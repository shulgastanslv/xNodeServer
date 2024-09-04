import logging
from websockets import ConnectionClosedError, ConnectionClosedOK, WebSocketServerProtocol, connect, serve
import json
import asyncio
from typing import Callable, Dict, Any
from behavior_tree import *
from store import xNodeStore

class Server(ABC):
    @abstractmethod
    async def run(self) -> xNodeResult:
        pass
    @abstractmethod
    async def handler(self, websocket: WebSocketServerProtocol) -> xNodeResult:
        pass

class xNodeServer(Server):
    
    def __init__(self, host: str = "localhost", port: int = 8765) -> None:
        
        self.behavior_trees: Dict[str, BehaviorTree] = {}
        self.host = host
        self.port = port
        self.store = xNodeStore()
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger()
    
    async def send_request_to_dispatchers(self, command: str, request: Dict[str, Any]) -> List[Dict[str, Any]]:
        results = []
        for websocket in self.store.active_connections:
            try:
                if not websocket.open:
                    self.logger.warning(f"Skipping closed websocket: {websocket.remote_address}")
                    continue

                message = {"command": command, **request}
                message_str = json.dumps(message)

                await websocket.send(message_str)
                self.logger.info(f"Sent to Dispatcher {websocket.remote_address}: {message_str}")

                response_str = await websocket.recv()
                self.logger.info(f"Received from Dispatcher {websocket.remote_address}: {response_str}")

                response = json.loads(response_str)
                results.append(response)
            except ConnectionClosedOK as e:
                self.logger.warning(f"Connection closed normally with {websocket.remote_address}: {str(e)}")
                self.store.active_connections.remove(websocket)
            except ConnectionClosedError as e:
                self.logger.error(f"Connection closed with error {websocket.remote_address}: {str(e)}")
                self.store.active_connections.remove(websocket)
            except Exception as e:
                self.logger.error(f"Error sending request to dispatcher {websocket.remote_address}: {str(e)}")

        return results

    async def handler(self, websocket: WebSocketServerProtocol) -> xNodeResult:
        self.store.active_connections.append(websocket)
        try:
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
        except ConnectionClosedOK as e:
            self.logger.info(f"Connection closed normally: {str(e)}")
        except ConnectionClosedError as e:
            self.logger.error(f"Connection closed with error: {str(e)}")
        finally:
            if websocket in self.store.active_connections:
                self.store.active_connections.remove(websocket)
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
            return await self._get_tree(request)
        elif command == "register_action":
            return await self._register_action(request)
        elif command == "register_condition":
            return await self._register_condition(request)
        elif command == "invoke_func":
            return await self._invoke_function(request)
        else:
            return {"status": "error", "message": f"Unknown command: {command}"}

    async def _register_action(self, request: Dict[str, Any]) -> Dict[str, Any]:
        self.logger.info(f"Registering action with request: {request}")
        name = request.get("name")
        if name:
            self.store.actions[name] = lambda: True  # Dummy implementation
            return {"status": "success", "message": f"Action '{name}' registered."}
        else:
            return {"status": "error", "message": "Invalid action registration request."}

    async def _register_condition(self, request: Dict[str, Any]) -> Dict[str, Any]:
        self.logger.info(f"Registering condition with request: {request}")
        name = request.get("name")
        if name:
            # Add condition registration logic here
            self.store.conditions[name] = lambda: False  # Dummy implementation
            return {"status": "success", "message": f"Condition '{name}' registered."}
        else:
            return {"status": "error", "message": "Invalid condition registration request."}
    
    async def _invoke_function(self, request: Dict[str, Any]) -> Dict[str, Any]:
        name = request.get("fnc_name")
        if not name:
            return {"status": "error", "message": "Function name not provided."}
        
        results = await self.send_request_to_dispatchers("invoke_func", {"name": name})
        
        return {"status": "success", "results": results}

    async def _create_tree(self, request: Dict[str, Any]) -> Dict[str, Any]:
        tree_id = request.get("tree_id")
        tree_structure = request.get("tree_structure")
        if tree_id and tree_structure:
            tree = self._create_tree_from_dict(tree_structure)
            self.store.behavior_trees[tree_id] = tree
            self.logger.info(f"Tree {tree_id} created.")
            return {"status": "success", "message": f"Tree {tree_id} created."}
        else:
            self.logger.warning("Invalid tree creation request.")
            return {"status": "error", "message": "Invalid tree creation request."}

    async def _run_tree(self, request: Dict[str, Any]) -> Dict[str, Any]:
        tree_id = request.get("tree_id")
        if tree_id in self.store.behavior_trees:
            tree = self.store.behavior_trees[tree_id]
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
        if tree_id in self.store.behavior_trees:
            tree = self.store.behavior_trees[tree_id]
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
        action = self.store.actions.get(action_name)
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
        condition = self.store.conditions.get(condition_name)
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
        async def handle_connection(websocket: WebSocketServerProtocol, path: str) -> None:
            await self.handler(websocket)
        async with serve(handle_connection, self.host, self.port):
            await asyncio.Future()
