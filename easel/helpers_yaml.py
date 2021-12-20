import os.path
import yaml

from easel import assignment
from easel import assignment_group
from easel import external_tool
from easel import module
from easel import page
from easel import quiz
from easel import quiz_question

# Define custom yaml tags
yaml.add_constructor("!Assignment", assignment.constructor)
yaml.add_constructor("!AssignmentGroup", assignment_group.constructor)
yaml.add_constructor("!ExternalTool", external_tool.constructor)
yaml.add_constructor("!Module", module.constructor)
yaml.add_constructor("!Page", page.constructor)
yaml.add_constructor("!Quiz", quiz.constructor)
yaml.add_constructor("!QuizQuestion", quiz_question.constructor)

def read(filepath):
    if os.path.isdir(filepath):
        return None
    with open(filepath) as f:
        return yaml.load(f, Loader=yaml.FullLoader)

def write(filepath, obj):
    if os.path.isdir(filepath):
        return None
    with open(filepath, 'w') as f:
        tag = f"!{obj.__class__.__name__}"
        fields = dict(obj)
        if obj.canvas_wrapper:
            fields = fields[obj.canvas_wrapper]
        data = yaml.dump(fields)
        out = f"{tag}\n{data}"
        f.write(out)

def construct_node(loader, node, class_):
    if isSequenceNode(node):
        seq = []
        for subnode in node.value:
            seq.append(construct_node(loader, subnode, class_))
        return seq
    elif isMappingNode(node):
        return class_(**loader.construct_mapping(node, deep=True))
    elif isScalarNode(node):
        return class_(loader.construct_scalar(node))
    else:
        raise ValueError(f"Invalid yaml node type {type(node)} for {node}")

def isSequenceNode(node):
    return isinstance(node, yaml.nodes.SequenceNode)

def isMappingNode(node):
    return isinstance(node, yaml.nodes.MappingNode)

def isScalarNode(node):
    return isinstance(node, yaml.nodes.ScalarNode)
