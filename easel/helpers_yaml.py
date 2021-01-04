import yaml

from easel import assignment
from easel import assignment_group
from easel import external_tool
from easel import module
from easel import page

# Define custom yaml tags
yaml.add_constructor("!Assignment", assignment.constructor)
yaml.add_constructor("!AssignmentGroup", assignment_group.constructor)
yaml.add_constructor("!ExternalTool", external_tool.constructor)
yaml.add_constructor("!Module", module.constructor)
yaml.add_constructor("!Page", page.constructor)

def read(filepath):
    with open(filepath) as f:
        return yaml.load(f, Loader=yaml.FullLoader)

def write(filepath, obj):
    with open(filepath, 'w') as f:
        f.write(yaml.dump(obj))
