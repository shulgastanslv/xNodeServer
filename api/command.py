from abc import ABC, ABCMeta, abstractmethod
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, Union
from dp_store import xNodeDpStore
from routes import Routes


class xNodeCommand(ABC):
    
    def __init__(self, route: Routes):
        self._route = route
    
    @property
    def route(self) -> Routes:
        return self._route

    @abstractmethod
    def execute(self, store : xNodeDpStore, name: str, func: Callable[[], Union[bool, Awaitable[bool]]]) -> bool:
        pass
    
class RegisterAction(xNodeCommand):
    def __init__(self):
        super().__init__(Routes.RegisterAction)
    
    def execute(self, store : xNodeDpStore, name: str, func: Callable[[], Union[bool, Awaitable[bool]]]) -> bool:
        return store.add_action(func)
        

class RegisterCondition(xNodeCommand):
    def __init__(self):
        super().__init__(Routes.RegisterCondition)

    
    def execute(self, store : xNodeDpStore, name: str, func: Callable[[], Union[bool, Awaitable[bool]]]) -> bool:
        return store.add_condition(func)
    