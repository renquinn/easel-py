import collections
import os.path
import yaml

from easel import assignment
from easel import assignment_group
from easel import external_tool
from easel import grading_scheme
from easel import module
from easel import navigation_tab
from easel import page
from easel import quiz
from easel import quiz_question

# Define custom yaml tags
yaml.add_constructor("!Assignment", assignment.constructor)
yaml.add_constructor("!AssignmentGroup", assignment_group.constructor)
yaml.add_constructor("!ExternalTool", external_tool.constructor)
yaml.add_constructor("!GradingScheme", grading_scheme.constructor)
yaml.add_constructor("!Module", module.constructor)
yaml.add_constructor("!NavigationTabs", navigation_tab.constructor)
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
    # write cleaner yaml using the representer functions defined below
    yaml.add_representer(str, str_representer)
    yaml.representer.SafeRepresenter.add_representer(str, str_representer) # safe_dump

    with open(filepath, 'w') as f:
        tag = f"!{obj.__class__.__name__}"
        data = obj.yaml()
        out = f"{tag}\n{data}"
        f.write(out)

def str_representer(dumper, data):
    '''Writes block strings for multiple lines, regular strings for single lines'''
    if len(data.splitlines()) > 1:  # check for multiline string
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)

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

def construct_ordered_mapping(loader, node):
    '''saves the field order in the file to correctly recreate the file later'''
    fields = loader.construct_mapping(node)
    fields['yaml_order'] = list(fields)
    return fields

def isSequenceNode(node):
    return isinstance(node, yaml.nodes.SequenceNode)

def isMappingNode(node):
    return isinstance(node, yaml.nodes.MappingNode)

def isScalarNode(node):
    return isinstance(node, yaml.nodes.ScalarNode)
