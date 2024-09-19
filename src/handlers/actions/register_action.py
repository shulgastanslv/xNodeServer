from typing import Any, Callable, Dict

from mediatr import Mediator
from common.result import xNodeResult
from common.status import xNodeStatus
from src.handlers.abstractions.command_handler import CommandHandler
from src.requests.actions.register_action import RegisterActionRequest

@Mediator.handler
class RegisterActionCommandHandler():
    def handle(self, request: RegisterActionRequest) -> xNodeResult:
        try:
            print(str(request.id))
            print(str(request.name))
            return xNodeResult(xNodeStatus.Success, True)
        except TypeError as e:
            return xNodeResult(xNodeStatus.Failure, False)