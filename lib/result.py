from status import xNodeStatus

class xNodeResult:
    def __init__(self, status, value=None, error=None):
        self.status = status
        self.value = value
        self.error = error

    def is_success(self):
        return self.status == xNodeStatus.Success

    def is_failure(self):
        return self.status == xNodeStatus.Failure

    def is_running(self):
        return self.status == xNodeStatus.Running

    def __repr__(self):
        return f"Result(status={self.status}, value={self.value}, error={self.error})"
