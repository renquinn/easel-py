from easel import component
from easel import course

MODULES_PATH=course.COURSE_PATH+"/modules"

class Module(component.Component):

    def __init__(self, name=None, published=None, position=None,
            unlock_at=None, require_sequential_progress=None,
            prerequisite_module_ids=None, items=None):
        component.Component.__init__(self, MODULES_PATH)
        self.name = name
        self.published = published
        self.position = position
        self.unlock_at = unlock_at
        self.require_sequential_progress = require_sequential_progress
        self.prerequisite_module_ids = prerequisite_module_ids
        # Items can only be added after the fact
	#self.items = items

    def __iter__(self):
        fields = dict(super().__iter__())
        wrapped = {"module": fields}
        yield from wrapped.items()

    def __repr__(self):
        return f"Module(name={self.name}, position={self.position})"

# Needed for custom yaml tag
def constructor(loader, node):
    return Module(**loader.construct_mapping(node))
