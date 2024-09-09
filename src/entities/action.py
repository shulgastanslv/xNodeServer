from dataclasses import dataclass, field
from datetime import datetime
from typing import Awaitable, Callable, List, Dict, Optional, Union

@dataclass
class Action:
    id: str
    func: Callable[[], Union[bool, Awaitable[bool]]]
    name: str
    repeat: bool = False
    repeat_count: int = 1
    execute_once: bool = False