from dataclasses import dataclass, field
from datetime import datetime
from typing import Awaitable, Callable, List, Dict, Optional, Union

@dataclass
class ContextEntry:
    id : str
    time : datetime = field(default_factory=datetime.now) 
    result : bool = False
    