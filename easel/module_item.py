import logging

from easel import component
from easel import canvas_id
from easel import files
from easel import helpers
from easel import helpers_yaml
from easel import module

MODULE_ITEMS_PATH=module.MODULE_PATH+"/items"
MODULE_ITEM_PATH=MODULE_ITEMS_PATH+"/{}"
MODULE_ITEMS_TABLE="module_items"
WRAPPER="module_item"
VALID_TYPES = ["File", "Page", "Discussion", "Assignment", "Quiz", "SubHeader",
        "ExternalUrl", "ExternalTool"]

class ModuleItem(component.Component):

    def __init__(self, item=None, title=None, type=None, content_id=None,
            position=None, indent=None, page_url=None, external_url=None,
            published=None, new_tab=None, filename=""):
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
        self.published = published

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

    def load_module(self, db, course_id):
        if self.filename:
            module_filename = self.filename.split('--')[0]
            m = helpers_yaml.read(module_filename)
            m.filename = module_filename
            return m

    def preprocess(self, db, course_, dry_run):
        if not self.item:
            # it should be a url or SubHeader so we only have to set the type
            # and filename
            if self.external_url:
                self.type = "ExternalUrl"
            else:
                self.type = "SubHeader"
            return
        cid = canvas_id.CanvasID(self.item, course_.canvas_id)
        cid.find_id(db)
        if self.item.startswith("files"):
            # TODO: need a better way to detect that this is a literal File to
            # link to and not just a yaml file containing item info such as for
            # a Page or Assignment
            self.type = "File"
            if not cid.canvas_id:
                # the file probably doesn't exist in the course so we need to
                # push it first
                files.push(db, course_, self.item, True, dry_run)
            return
        item = helpers_yaml.read(self.item)
        item.filename = self.item
        if not cid.canvas_id:
            # the component probably doesn't exist in the course so we need to
            # push it first
            item.push(db, course_, dry_run)
        if not self.title:
            self.title = getattr(item, "name", getattr(item, "title", self.item))
        type_ = type(item).__name__
        if type_ not in VALID_TYPES:
            raise ValueError(f"Cannot add an item of type {type_} to a module."
                    " Can be one of {VALID_TYPES}")
        self.type = type_
        cid = item.get_canvas_id(db, course_.canvas_id)
        if self.type == "Page":
            self.page_url = cid
        else:
            self.content_id = cid

    def postprocess(self, db, course_, dry_run):
        course_id = course_.canvas_id
        if self.type not in ["ExternalUrl", "SubHeader"]:
            return
        cid = canvas_id.CanvasID(self.filename, course_id)
        cid.find_id(db)
        if not cid.canvas_id:
            print(f"Failed to publish {self}, we don't "
                    "have a canvas id for it")
            print("Make sure the module item was succesfully pushed to Canvas")
            return
        # since Canvas doesn't allow you to publish some ModuleItems
        # (ExternalUrl, SubHeader) on creation, we'll update the same item here
        # to make sure it gets published (if desired; when 'published' is False
        # it won't be published)
        parent_module = self.load_module(db, course_id)
        path = self.format_update_path(db, course_id, cid.canvas_id, parent_module)
        self.preprocess(db, course_id, dry_run)
        resp = helpers.put(path, self, dry_run=dry_run)
        if "errors" in resp:
            print(f"failed to publish {self}")
            for error in resp['errors']:
                logging.error(error['message'])
