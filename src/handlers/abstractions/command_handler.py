
from abc import ABC, abstractmethod
from typing import Any, Dict

from common.result import xNodeResult


class CommandHandler(ABC):
    @abstractmethod
    async def handle(self, request: Any) -> xNodeResult:
        raise NotImplementedError()