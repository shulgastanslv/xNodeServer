import asyncio
from typing import Callable, Dict, Optional, Union
from app.behavior_tree import ActionNode, ConditionNode, Node

class xNodeLoader:
    def __init__(self) -> None:
        self.actions: Dict[str, Callable[[], Union[bool, asyncio.Future[bool]]]] = {}
        self.conditions: Dict[str, Callable[[], Union[bool, asyncio.Future[bool]]]] = {}

    def add_action(self, name: str, action: Callable[[], Union[bool, asyncio.Future[bool]]]) -> None:
        self.actions[name] = action

    def add_condition(self, name: str, condition: Callable[[], Union[bool, asyncio.Future[bool]]]) -> None:
        self.conditions[name] = condition

    def get_action(self, name: str) -> Optional[Callable[[], Union[bool, asyncio.Future[bool]]]]:
        return self.actions.get(name)
    
    def get_actions(self) -> Optional[Callable[[], Union[bool, asyncio.Future[bool]]]]:
        return self.actions.keys()

    def get_conditions(self) -> Optional[Callable[[], Union[bool, asyncio.Future[bool]]]]:
        return self.conditions.keys()

    def get_condition(self, name: str) -> Optional[Callable[[], Union[bool, asyncio.Future[bool]]]]:
        return self.conditions.get(name)

    def create_action_node(self, name: str, repeat: bool = False, repeat_count: int = 1, execute_once: bool = False) -> Optional[Node]:
        action = self.get_action(name)
        if action:
            return ActionNode(action, repeat, repeat_count, execute_once)
        return None

    def create_condition_node(self, name: str) -> Optional[Node]:
        condition = self.get_condition(name)
        if condition:
            return ConditionNode(condition)
        return None