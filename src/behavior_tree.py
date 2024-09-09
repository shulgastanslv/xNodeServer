from abc import ABC, abstractmethod
import asyncio
from dataclasses import asdict
from typing import Any, Awaitable, Callable, Dict, List, Optional, Union
from common.error import xNodeError
from common.result import xNodeResult, xNodeStatus
from src.entities.action import Action
from src.entities.condition import Condition
from src.entities.context import ContextEntry

class Context:
    def __init__(self) -> None:
        self._history: List[ContextEntry] = []

    def save(self, entry : ContextEntry) -> None:
        if entry.id not in self._history:
            self._history.append(entry)
            
    def update(self, entry : ContextEntry) -> bool:
        for entry in self._history:
            if entry.id == entry.id:
                entry.result = entry.result
                entry.time = datetime.now()
                return True
        self.save(entry)
            
    def remove(self, action_id: str) -> None:
        self._history = [entry for entry in self._history if entry.id != action_id]
          
    def get(self, template: Optional[Callable[[ContextEntry], bool]] = None) -> List[ContextEntry]:
        if template is None:
            return self._history.copy()
        else:
            return [entry for entry in self._history if template(entry)]
    
    def has_completed(self, action_id: str) -> bool:
        return any(entry.id == action_id for entry in self._history)
    
    def clear(self) -> None:
        self._history.clear()
        
    def __repr__(self) -> str:
         return '\n'.join(repr(entry) for entry in self._history)
class Node(ABC):
    @abstractmethod
    async def tick(self, context: Context) -> xNodeResult:
        raise NotImplementedError()
class ActionNode(Node):
    def __init__(self, action : Action) -> None:
        self.child : Action = action

    async def tick(self, context: Context) -> xNodeResult:
        id: str = self.child.id
        
        if self.child.execute_once and context.has_completed(id):
            return xNodeResult(xNodeStatus.Success, True)
        
        if self.child.repeat:
            for _ in range(self.child.repeat_count):
                result = await self.__execute_action()
                context.save(ContextEntry(id=self.child.id, time=datetime.now(), result=result))
                if result.is_failure():
                    return result
            return xNodeResult(xNodeStatus.Success, True)
        else:
            result = await self.__execute_action()
            context.save(ContextEntry(id=self.child.id, time=datetime.now(), result=result))
            return result
    
    async def __execute_action(self) -> xNodeResult:
        result = self.child.func()
        if asyncio.iscoroutine(result):
            result = await result
        return xNodeResult(xNodeStatus.Success, True) if result else xNodeResult(xNodeStatus.Failure, False)
    
    def __repr__(self) -> str:
        return f"{asdict(self.child)}"
class ConditionNode(Node):
    def __init__(self, condition: Condition) -> None:
        self.child = condition

    async def tick(self, context: Context) -> xNodeResult:
        result = await self.__evaluate_condition()
        context.save(ContextEntry(id=self.child.id, time=datetime.now(), result=result))
        return xNodeResult(xNodeStatus.Success, True) if result else xNodeResult(xNodeStatus.Failure, False)

    async def __evaluate_condition(self) -> xNodeResult:
        if asyncio.iscoroutinefunction(self.child.func):
            result = await self.child.func()
        else:
            result = self.child.func()
        return xNodeResult(xNodeStatus.Success, True) if result else xNodeResult(xNodeStatus.Failure, False)

    def __repr__(self) -> str:
        return f"{asdict(self.child)}"
class SequenceNode(Node):
    def __init__(self, children: List[Node]) -> None:
        self.children = children
        self.current_index = 0

    async def tick(self, context: Context) -> xNodeResult:
        while self.current_index < len(self.children):
            result = await self.children[self.current_index].tick(context)
            if result.is_running():
                return xNodeResult(xNodeStatus.Running)
            elif result.is_failure():
                self.current_index = 0
                return xNodeResult(xNodeStatus.Failure, False)
            self.current_index += 1
        self.current_index = 0
        return xNodeResult(xNodeStatus.Success, True)

    def __repr__(self) -> str:
        return f"{self.children}"
class SelectorNode(Node):
    def __init__(self, children: List[Node]) -> None:
        self.children = children
        self.current_index = 0

    async def tick(self, context: Context) -> xNodeResult:
        while self.current_index < len(self.children):
            result = await self.children[self.current_index].tick(context)
            if result.is_running():
                return xNodeResult(xNodeStatus.Running)
            elif result.is_success():
                self.current_index = 0
                return xNodeResult(xNodeStatus.Success, True)
            self.current_index += 1
        self.current_index = 0
        return xNodeResult(xNodeStatus.Failure, False)

    def __repr__(self) -> str:
        return f"{self.children}"
class ParallelNode(Node):
    def __init__(self, children: List[Node], success_threshold: int) -> None:
        self.children = children
        self.success_threshold = success_threshold

    async def tick(self, context: Context) -> xNodeResult:
        success_count = 0
        failure_count = 0
        for child in self.children:
            result = await child.tick(context)
            if result.is_success():
                success_count += 1
            elif result.is_failure():
                failure_count += 1
            if success_count >= self.success_threshold:
                return xNodeResult(xNodeStatus.Success, True)
            elif failure_count > len(self.children) - self.success_threshold:
                return xNodeResult(xNodeStatus.Failure, False)
        return xNodeResult(xNodeStatus.Running)

    def __repr__(self) -> str:
        return f"{self.children}{self.success_threshold}"
class InvertDecorator(Node):
    def __init__(self, child: Node) -> None:
        self.child = child

    async def tick(self, context: Context) -> xNodeResult:
        result = await self.child.tick(context)
        if result.is_success():
            return xNodeResult(xNodeStatus.Failure, False)
        elif result.is_failure():
            return xNodeResult(xNodeStatus.Success, True)
        return result

    def __repr__(self) -> str:
        return f"{self.child}"
class RepeatDecorator(Node):
    def __init__(self, child: Node, repeat_count: int) -> None:
        self.child = child
        self.repeat_count = repeat_count

    async def tick(self, context: Context) -> xNodeResult:
        for _ in range(self.repeat_count):
            result = await self.child.tick(context)
            if result.is_failure():
                return result
        return xNodeResult(xNodeStatus.Success, True)

    def __repr__(self) -> str:
        return f"{self.child} (repeat {self.repeat_count} times)"
class TimeoutDecorator(Node):
    def __init__(self, child: Node, timeout: float) -> None:
        self.child = child
        self.timeout = timeout

    async def tick(self, context: Context) -> xNodeResult:
        try:
            result = await asyncio.wait_for(self.child.tick(context), timeout=self.timeout)
        except asyncio.TimeoutError:
            return xNodeResult(xNodeStatus.Failure, False)
        return result

    def __repr__(self) -> str:
        return f"{self.child} (timeout {self.timeout} seconds)"
class RepeatUntilSuccessDecorator(Node):
    def __init__(self, child: Node, max_retries: int = 10) -> None:
        self.child = child
        self.max_retries = max_retries

    async def tick(self, context: Context) -> xNodeResult:
        attempts = 0
        while attempts < self.max_retries:
            result = await self.child.tick(context)
            if result.is_success():
                return xNodeResult(xNodeStatus.Success, True)
            attempts += 1
        return xNodeResult(xNodeStatus.Failure, False)
    
    def __repr__(self) -> str:
        return f"{self.child} (repeat until success, max retries: {self.max_retries})"
class BehaviorTree:
    def __init__(self, root: Optional[Node] = None) -> None:
        self.root = root
        self.context = Context()

    def update(self, root: Node) -> None:
        self.root = root

    async def run(self) -> None:
        if not self.root:
            raise xNodeError("Root node is not set for the behavior tree.")
        result = await self.root.tick(self.context)
        if result.is_success():
            return xNodeResult(xNodeStatus.Success, True)
        elif result.is_failure():
            return xNodeResult(xNodeStatus.Failure, False)
        elif result.is_running():
            return xNodeResult(xNodeStatus.Running)

    def __repr__(self) -> str:
        return f"{self.root}{self.context})"