from flask import Blueprint, jsonify, render_template, redirect, request
from app.behavior_tree import ActionNode, BehaviorTree, ConditionNode, SequenceNode
from app.loader import xNodeLoader

home = Blueprint("home", __name__, template_folder="templates")
loader = xNodeLoader()

@home.route("/actions")
def list_actions():
     return jsonify({"actions" : list(loader.get_actions())})

@home.route("/conditions")
def list_conditions():
    return jsonify({"conditions" : list(loader.get_conditions())})

@home.route("/create_tree")
def create_tree():
    tree = BehaviorTree()
    return jsonify({
        "status": "Tree created successfully!",
        "tree": tree.to_dict()})