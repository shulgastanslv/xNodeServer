from enum import Enum

class Routes(Enum):
    RegisterAction = "register_action",
    CreateTree = "create_tree",
    RegisterFallback  = "register_fallback",
    RegisterParallel  = "register_parallel",
    DeleteTree  = "delete_tree",
    RunTree  = "run_tree",
    StopTree  = "stop_tree",
    UpdateTree  = "update_tree",
    DeleteAllTree  = "delete_all_tree",
    RegisterCondition  = "register_condition",
    InvokeFunction = "invoke_func"