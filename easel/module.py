from easel import component
from easel import course

MODULES_PATH=course.COURSE_PATH+"/modules"
MODULE_PATH=MODULES_PATH+"/{}"
MODULES_TABLE="modules"
WRAPPER="module"

class Module(component.Component):

    def __init__(self, name=None, published=None, position=None,
            unlock_at=None, require_sequential_progress=None,
            prerequisite_module_ids=None, items=None, filename=""):
        super().__init__(create_path=MODULES_PATH, update_path=MODULE_PATH,
                db_table=MODULES_TABLE, canvas_wrapper=WRAPPER,
                filename=filename)
        self.name = name
        self.published = published
        self.position = position
        self.unlock_at = unlock_at
        self.require_sequential_progress = require_sequential_progress
        self.prerequisite_module_ids = prerequisite_module_ids
        # Items can only be added after the fact
	#self.items = items

    def __repr__(self):
        return f"Module(name={self.name}, position={self.position})"

# Needed for custom yaml tag
def constructor(loader, node):
    return Module(**loader.construct_mapping(node))
