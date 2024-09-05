from typing import Awaitable, Callable, Dict, Union


class xNodeDpStore:
    def __init__(self) -> None:
        self.actions: Dict[str, Callable[[], Union[bool, Awaitable[bool]]]] = {}
        self.conditions: Dict[str, Callable[[], Union[bool, Awaitable[bool]]]] = {}
    
    def add_action(self, name: str, action: Callable[[], Union[bool, Awaitable[bool]]]) -> bool:
        if name in self.actions:
            return False 
        self.actions[name] = action
        return True
    
    def add_condition(self, name: str, condition: Callable[[], Union[bool, Awaitable[bool]]]) -> bool:
        if name in self.conditions:
            return False
        self.conditions[name] = condition
        return True
        
        
        
        
        
        