from abc import ABC, abstractmethod
import asyncio
from dataclasses import asdict
from typing import Any, Awaitable, Callable, Dict, List, Optional, Union
import inspect
from injector import inject
from functools import singledispatch, singledispatchmethod, wraps
from common.error import xNodeError
from common.result import xNodeResult, xNodeStatus
from src.entities import Action
from src.node_type import NodeType

class BehaviorTreeContext:
    def __init__(self) -> None:
        self._completed_actions: List[str] = []

    def save(self, action_id: str) -> None:
        if action_id not in self._completed_actions:
            self._completed_actions.append(action_id)
    
    def get_completed_actions(self) -> List[str]:
        return self._completed_actions.copy()

class Node(ABC):
    @abstractmethod
    async def tick(self, context: BehaviorTreeContext) -> xNodeResult:
        pass
    

class ActionNode(Node):
    def __init__(self, action : Action) -> None:
        self.child : Action = action

    async def tick(self, context: BehaviorTreeContext) -> xNodeResult:
        id : str = self.child.id
        
        if self.execute_once and id in context.get_completed_actions():
            return xNodeResult(xNodeStatus.Success)
        
        if self.child.repeat:
            for _ in range(self.child.repeat_count):
                result = await self.__execute_action()
                if result.is_failure():
                    return result
            return xNodeResult(xNodeStatus.Success)
        else:
            return await self.__execute_action()
    
    async def __execute_action(self) -> xNodeResult:
        result = self.child.func()
        if asyncio.iscoroutine(result):
            result = await result
        return xNodeResult(xNodeStatus.Success) if result else xNodeResult(xNodeStatus.Failure)
    
    def __repr__(self) -> str:
        return f"{asdict(self.action)}"
    






class ConditionNode(Node):
    def __init__(self, condition: Callable[[], Union[bool, Awaitable[bool]]]) -> None:
        self.condition = condition

    async def tick(self, context: BehaviorTreeContext) -> xNodeResult:
        if asyncio.iscoroutinefunction(self.condition):
            result = await self.condition()
        else:
            result = self.condition()
        return xNodeResult(xNodeStatus.Success) if result else xNodeResult(xNodeStatus.Failure)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'type': 'ConditionNode',
            'condition': self.condition.__name__
        }

class SequenceNode(Node):
    def __init__(self, children: List[Node]) -> None:
        self.children = children
        self.current_index = 0

    async def tick(self, context: BehaviorTreeContext) -> xNodeResult:
        while self.current_index < len(self.children):
            result = await self.children[self.current_index].tick(context)
            if result.is_running():
                return xNodeResult(xNodeStatus.Running)
            elif result.is_failure():
                self.current_index = 0
                return xNodeResult(xNodeStatus.Failure)
            self.current_index += 1
        self.current_index = 0
        return xNodeResult(xNodeStatus.Success)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'type': 'SequenceNode',
            'children': [child.to_dict() for child in self.children]
        }

class SelectorNode(Node):
    def __init__(self, children: List[Node]) -> None:
        self.children = children
        self.current_index = 0

    async def tick(self, context: BehaviorTreeContext) -> xNodeResult:
        while self.current_index < len(self.children):
            result = await self.children[self.current_index].tick(context)
            if result.is_running():
                return xNodeResult(xNodeStatus.Running)
            elif result.is_success():
                self.current_index = 0
                return xNodeResult(xNodeStatus.Success)
            self.current_index += 1
        self.current_index = 0
        return xNodeResult(xNodeStatus.Failure)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'type': 'SelectorNode',
            'children': [child.to_dict() for child in self.children]
        }

class ParallelNode(Node):
    def __init__(self, children: List[Node], success_threshold: int) -> None:
        self.children = children
        self.success_threshold = success_threshold

    async def tick(self, context: BehaviorTreeContext) -> xNodeResult:
        success_count = 0
        for child in self.children:
            result = await child.tick(context)
            if result.is_success():
                success_count += 1
            elif result.is_running():
                return xNodeResult(xNodeStatus.Running)
        return xNodeResult(xNodeStatus.Success) if success_count >= self.success_threshold else xNodeResult(xNodeStatus.Failure)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'type': 'ParallelNode',
            'children': [child.to_dict() for child in self.children],
            'success_threshold': self.success_threshold
        }

class InvertDecorator(Node):
    def __init__(self, child: Node) -> None:
        self.child = child

    async def tick(self, context: BehaviorTreeContext) -> xNodeResult:
        result = await self.child.tick(context)
        if result.is_success():
            return xNodeResult(xNodeStatus.Failure)
        elif result.is_failure():
            return xNodeResult(xNodeStatus.Success)
        return result
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'type': 'InvertDecorator',
            'child': self.child.to_dict()
        }

class BehaviorTree:
    def __init__(self) -> None:
        self.root: Optional[Node] = None
        self.context = BehaviorTreeContext()

    def update(self, root: Node, context: Optional[BehaviorTreeContext] = None) -> None:
        self.root = root
        if context is not None:
            self.context = context

    async def run(self) -> None:
        if self.root is None:
            raise xNodeError("The root node of the behavior tree is not set!")

        result = await self.root.tick(self.context)
        self._handle_result(result)

    def _handle_result(self, result: xNodeResult) -> None:
        if result.is_failure():
            print(f"Behavior tree execution failed with error: {result.error}")
        elif result.is_running():
            print("Behavior tree is still running!")
        else:
            print("Behavior tree executed successfully!")
            
    def to_dict(self) -> Dict[str, Any]:
        if self.root is None:
            return {}
        return {
            'root': self.root.to_dict(),
            'context': {
                'completed_actions': self.context.get_completed_actions()
            }
        }