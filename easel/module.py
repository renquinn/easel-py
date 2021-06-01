from easel import canvas_id
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
        self.items = items

    def __repr__(self):
        return f"Module(name={self.name}, position={self.position})"

    def postprocess(self, db, course_id, dry_run):
        cid = canvas_id.CanvasID(self.filename, course_id)
        cid.find_id(db)
        if not cid.canvas_id:
            print(f"failed to add ModuleItems to Module {self}, we don't "
                    "have a canvas id for it")
            print("make sure the module has first been pushed to Canvas")
            return

        for item in self.items:
            if isinstance(item, dict):
                item["filename"] = f"{self.filename}--{item['item']}"
                item_component = component.build("ModuleItem", item)
            elif isinstance(item, str):
                item_component = component.build("ModuleItem", {
                    "item": item,
                    "filename": f"{self.filename}--{item}"})
            else:
                raise TypeError(f"Invalid item specification on module {self}")

            print(f"\tpushing ModuleItem {item_component} to Module {self}")
            item_component.push(db, course_id, dry_run, parent_component=self)

# Needed for custom yaml tag
def constructor(loader, node):
    return Module(**loader.construct_mapping(node))
