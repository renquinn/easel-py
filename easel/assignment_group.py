from easel import component
from easel import course

ASSIGN_GROUP_PATH=course.COURSE_PATH+"/assignment_groups"

class AssignmentGroup(component.Component):

    def __init__(self, name="", position=-1, group_weight=-1):
        component.Component.__init__(self, ASSIGN_GROUP_PATH)
        self.name = name
        self.position = position
        self.group_weight = group_weight

    def __repr__(self):
        return (f"AssignmentGroup(name={self.name}, position={self.position},"
                f" weight={self.group_weight})")

# Needed for custom yaml tag
def constructor(loader, node):
    return AssignmentGroup(**loader.construct_mapping(node))
