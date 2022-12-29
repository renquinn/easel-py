from tqdm import tqdm

from easel import canvas_id
from easel import component
from easel import course
from easel import helpers
from easel import helpers_yaml

ASSIGN_GROUPS_PATH=course.COURSE_PATH+"/assignment_groups"
ASSIGN_GROUP_PATH=ASSIGN_GROUPS_PATH+"/{}"
ASSIGN_GROUPS_TABLE="assignment_groups"
ASSIGN_GROUPS_DIR="assignment_groups"

class AssignmentGroup(component.Component):

    def __init__(self, name="", position=-1, group_weight=-1, filename="",
            yaml_order=[]):
        super().__init__(create_path=ASSIGN_GROUPS_PATH,
                update_path=ASSIGN_GROUP_PATH, db_table=ASSIGN_GROUPS_TABLE,
                filename=filename, yaml_order=yaml_order)
        self.name = name
        self.position = position
        self.group_weight = group_weight

    def __repr__(self):
        return (f"AssignmentGroup(name={self.name}, position={self.position},"
                f" weight={self.group_weight})")

    @classmethod
    def build(cls, fields):
        desired_fields = cls.__init__.__code__.co_varnames[1:]
        component.filter_fields(fields, desired_fields)
        return AssignmentGroup(**fields)

def pull_all(db, course_, dry_run):
    r = helpers.get(ASSIGN_GROUPS_PATH.format(course_.canvas_id),
            dry_run=dry_run)
    ags = []
    for ag in tqdm(r):
        cid = canvas_id.find_by_id(db, course_.canvas_id, ag.get('id'))
        if cid:
            ag['filename'] = cid.filename
        else:
            ag['filename'] = component.gen_filename(ASSIGN_GROUPS_DIR, ag.get('name',''))
            cid = canvas_id.CanvasID(ag['filename'], course_.canvas_id)
            cid.canvas_id = ag.get('id')
            cid.save(db)
        ags.append(AssignmentGroup.build(ag))
    return ags

# Needed for custom yaml tag
def constructor(loader, node):
    fields = helpers_yaml.construct_ordered_mapping(loader, node)
    return AssignmentGroup(**fields)
