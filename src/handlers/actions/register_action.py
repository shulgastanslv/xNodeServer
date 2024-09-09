from typing import Any, Callable, Dict
from common.result import xNodeResult
from common.status import xNodeStatus
from src.handlers.abstractions.command_handler import CommandHandler
from src.requests.actions.register_action import RegisterActionRequest


class RegisterActionCommandHandler(CommandHandler):
    def __init__(self, actions: Dict[str, Callable]) -> None:
        self.actions = actions

    async def handler(self, request: Any) -> xNodeResult:
        try:
            request = RegisterActionRequest(**request)
            if request:
                self.actions[request.id] = request.name
                return xNodeResult(xNodeStatus.Success, True)
            else:
                return xNodeResult(xNodeStatus.Failure, False)
        except TypeError as e:
            return xNodeResult(xNodeStatus.Failure, False)