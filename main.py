from src.behavior_tree import *

action = Action('1', lambda : True, 'test')
action_node = ActionNode(action) 
print(action_node.child.id)    