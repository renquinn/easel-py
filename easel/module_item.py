from easel import component
from easel import canvas_id
from easel import helpers_yaml
from easel import module

MODULE_ITEMS_PATH=module.MODULE_PATH+"/items"
MODULE_ITEM_PATH=MODULE_ITEMS_PATH+"/{}"
MODULE_ITEMS_TABLE="module_items"
WRAPPER="module_item"
VALID_TYPES = ["File", "Page", "Discussion", "Assignment", "Quiz", "SubHeader",
        "ExternalUrl", "ExternalTool"]

class ModuleItem(component.Component):

    def __init__(self, item="", title=None, type=None, content_id=None,
            position=None, indent=None, page_url=None, external_url=None,
            new_tab=None, filename=""):
        super().__init__(create_path=MODULE_ITEMS_PATH, update_path=MODULE_ITEM_PATH,
                db_table=MODULE_ITEMS_TABLE, canvas_wrapper=WRAPPER,
                filename=filename)
        self.item = item
        self.title = title
        self.type = type
        self.content_id = content_id
        self.position = position
        self.indent = indent
        self.page_url = page_url
        self.external_url = external_url
        self.new_tab = new_tab

    def __repr__(self):
        return f"ModuleItem(item={self.item}, type={self.type}, title={self.title})"

    def format_create_path(self, db, *path_args):
        """2 args -> course_id, module_id"""
        course_id = path_args[0]
        cid = canvas_id.CanvasID(path_args[1].filename, course_id)
        cid.find_id(db)
        return self.create_path.format(course_id, cid.canvas_id)

    def format_update_path(self, db, *path_args):
        """3 args -> course_id, module_id, module_item_id"""
        course_id = path_args[0]
        cid = canvas_id.CanvasID(path_args[2].filename, course_id)
        cid.find_id(db)
        return self.update_path.format(course_id, cid.canvas_id, path_args[1])

    def preprocess(self, db, course_id, dry_run):
        item = helpers_yaml.read(self.item)
        item.filename = self.item
        if not self.title:
            self.title = getattr(item, "name", getattr(item, "title", self.item))
        type_ = type(item).__name__
        if type_ not in VALID_TYPES:
            raise ValueError(f"Cannot add an item of type {type_} to a module."
                    " Can be one of {VALID_TYPES}")
        self.type = type_
        cid = item.get_canvas_id(db, course_id)
        if self.type == "Page":
            self.page_url = cid
        else:
            self.content_id = cid
