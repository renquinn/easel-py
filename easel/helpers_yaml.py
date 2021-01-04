import yaml

import assignment
import assignment_group
import external_tool
import page

# Define custom yaml tags
yaml.add_constructor("!Assignment", assignment.constructor)
yaml.add_constructor("!AssignmentGroup", assignment_group.constructor)
yaml.add_constructor("!ExternalTool", external_tool.constructor)
yaml.add_constructor("!Page", page.constructor)

def read(filepath):
    with open(filepath) as f:
        return yaml.load(f, Loader=yaml.FullLoader)

def write(filepath, obj):
    with open(filepath, 'w') as f:
        f.write(yaml.dump(obj))
