from abc import ABC, ABCMeta, abstractmethod
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, Union
from dp_store import xNodeDpStore

    
class Routes(Enum):
    RegisterAction = "register_action",
    CreateTree = "create_tree",
    RegisterFallback  = "register_fallback",
    RegisterParallel  = "register_parallel",
    DeleteTree  = "delete_tree",
    RunTree  = "run_tree",
    StopTree  = "stop_tree",
    UpdateTree  = "update_tree",
    DeleteAllTree  = "delete_all_tree",
    RegisterCondition  = "register_condition",
    InvokeFunction = "invoke_func"
    

class xNodeCommand(ABC):
    
    @property
    @abstractmethod
    def route(self):
        pass

    @abstractmethod
    def execute(self, store : xNodeDpStore, name: str, func: Callable[[], Union[bool, Awaitable[bool]]]) -> bool:
        pass
    
class RegisterAction(xNodeCommand):
    @property
    def route(self):
        return Routes.RegisterAction
    
    def execute(self, store : xNodeDpStore, name: str, func: Callable[[], Union[bool, Awaitable[bool]]]) -> bool:
        return store.add_action(func)

class RegisterCondition(xNodeCommand):
    @property
    def route(self):
        return Routes.RegisterCondition
    
    def execute(self, store : xNodeDpStore, name: str, func: Callable[[], Union[bool, Awaitable[bool]]]) -> bool:
        return store.add_condition(func)
    