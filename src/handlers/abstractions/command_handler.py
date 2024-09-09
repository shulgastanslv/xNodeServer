
from abc import ABC, abstractmethod
from typing import Any, Dict

from common.result import xNodeResult


class CommandHandler(ABC):
    @abstractmethod
    async def handler(self, request: Any) -> xNodeResult:
        raise NotImplementedError()