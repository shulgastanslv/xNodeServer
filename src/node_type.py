from enum import Enum

class NodeType(Enum):
    ActionNode = 0,
    ConditionNode = 1,
    SequenceNode = 2,
    SelectorNode = 3,
    ParallelNode = 4,
    InvertDecorator = 5,