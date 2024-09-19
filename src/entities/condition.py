from dataclasses import dataclass, field
from datetime import datetime
from typing import Awaitable, Callable, List, Dict, Optional, Union

@dataclass
class Condition:
    id : str
    name : str
