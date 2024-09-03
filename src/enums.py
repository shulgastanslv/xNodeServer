from enum import Enum
from behavior_tree import *

class NodeType(Enum):
    ActionNode = str(ActionNode.__name__)
    ConditionNode =  str(ConditionNode.__name__)
    SequenceNode = str(SequenceNode.__name__)
    SelectorNode = str(SelectorNode.__name__)
    ParallelNode =  str(ParallelNode.__name__)
    InvertDecorator = str(InvertDecorator.__name__)
    
    

