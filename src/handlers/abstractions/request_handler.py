
from abc import ABC, abstractmethod
from typing import Any

from common.result import xNodeResult


class RequestHandler(ABC):
    @abstractmethod
    async def handle(self, request: Any) -> xNodeResult:
        raise NotImplementedError()