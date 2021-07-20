import logging
import os.path
import urllib.parse

from easel import assignment
from easel import canvas_id
from easel import component
from easel import course
from easel import files
from easel import helpers
from easel import page
from easel import quiz

MODULES_PATH=course.COURSE_PATH+"/modules"
MODULE_PATH=MODULES_PATH+"/{}"
MODULES_TABLE="modules"
MODULES_DIR="modules"
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
        # Items can only be added after the fact (unless pulling)
        self.items = items

    def __repr__(self):
        return f"Module(name={self.name}, position={self.position})"

    @classmethod
    def build(cls, fields):
        extras = ["id", "workflow_state", "items_count", "items_url", "state",
                "completed_at", "publish_final_grade"]
        defaults = [("require_sequential_progress", False),
                ("prerequisite_module_ids", []),
                ("unlock_at", "")]
        component.filter_fields(fields, extras, defaults)
        return Module(**fields)

    def postprocess(self, db, course_, dry_run):
        course_id = course_.canvas_id
        cid = canvas_id.CanvasID(self.filename, course_id)
        cid.find_id(db)
        if not cid.canvas_id:
            print(f"failed to add ModuleItems to Module {self}, we don't "
                    "have a canvas id for it")
            print("make sure the module has first been pushed to Canvas")
            return

        for i in range(len(self.items)):
            item = self.items[i]
            if isinstance(item, dict):
                # yaml objects (dictionaries) should be properly formatted
                if self.filename and 'item' in item:
                    item["filename"] = f"{self.filename}--{item['item']}"
                elif'external_url' in item:
                    # URL
                    item["filename"] = f"{self.filename}--{item['external_url']}"
                    if 'published' not in item:
                        item['published'] = True
                elif 'title' in item:
                    # SubHeader
                    item["filename"] = f"{self.filename}--{item['title']}"
                    if 'published' not in item:
                        item['published'] = True
                item["position"] = i+1
                item_component = component.build("ModuleItem", item)
            elif isinstance(item, str):
                # possible string-only options: filename, url, SubHeader
                base_item = {
                        "filename": f"{self.filename}--{item}",
                        "position": i+1
                        }
                if os.path.isfile(item):
                    base_item['item'] = item
                elif helpers.isurl(item):
                    base_item["external_url"] = item
                    # if title is blank, canvas says "No Title" on the module
                    # item, displaying the url instead seems like a better
                    # default
                    base_item["title"] = item
                    base_item["published"] = True
                else:
                    # assume SubHeader
                    base_item["title"] = item
                    base_item["published"] = True
                item_component = component.build("ModuleItem", base_item)
            else:
                raise TypeError(f"Invalid item specification on module {self}")

            print(f"\tpushing {item_component} to {self}")
            item_component.push(db, course_, dry_run, parent_component=self)

# Needed for custom yaml tag
def constructor(loader, node):
    return Module(**loader.construct_mapping(node))

def build_item(item, indent=0):
    if indent == 0:
        return item
    return {'item': item, 'indent': indent}

def pull_all(db, course_, dry_run):
    modules = []
    m = helpers.get(MODULES_PATH.format(course_.canvas_id),
            params={'include': ['items']}, dry_run=dry_run)
    for module_ in m:
        if 'items' not in module_ or not module_['items']:
            items_path = urllib.parse.urlparse(module_['items_url']).path
            module_['items'] = helpers.get(items_path, dry_run=dry_run)
        cid = canvas_id.find_by_id(db, course_.canvas_id, module_.get('id'))
        if cid:
            module_['filename'] = cid.filename
        else:
            module_['filename'] = component.gen_filename(MODULES_DIR,
                    str(module_.get('position')) + '-' + module_.get('name',''))
            cid = canvas_id.CanvasID(module_['filename'], course_.canvas_id)
            cid.canvas_id = module_.get('id')
            cid.save(db)

        items = {}
        for item in module_['items']:
            item_id = 0
            if item['type'] == "Page":
                item_id = item['page_url']
            elif item['type'] in ['File', 'Assignment', 'Quiz']:
                item_id = item['content_id']
            # SubHeaders and ExternalUrls won't be in the db anyway
            icid = canvas_id.find_by_id(db, course_.canvas_id, item_id)
            if item_id == 0 or not icid:
                # we don't have the item locally so try to pull it
                if item['type'] == "Page":
                    _, icid = page.pull_page(db, course_.canvas_id,
                            item['page_url'], dry_run)
                elif item['type'] == "File":
                    # get file info
                    file_path = urllib.parse.urlparse(item['url']).path
                    file_ = helpers.get(file_path, dry_run=dry_run)
                    url = file_['url']
                    # get parent folder info
                    folder_path = files.COURSE_FOLDERS_PATH.format(course_.canvas_id)+"/"+str(file_['folder_id'])
                    folder = helpers.get(folder_path, dry_run=dry_run)
                    path = folder['full_name'][len("course "):]
                    filepath = path + file_['filename']
                    # download the file
                    icid = files.pull_file(db, course_.canvas_id, url, file_['id'], filepath)
                elif item['type'] == 'Assignment':
                    _, icid = assignment.pull(db, course_, item_id, dry_run)
                elif item['type'] == 'Quiz':
                    _, icid = quiz.pull(db, course_, item, dry_run)
                elif item['type'] == 'SubHeader':
                    built_item = {'title': item['title']}
                    if not item['published']:
                        built_item['published'] = False
                elif item['type'] == 'ExternalUrl':
                    built_item = {
                        'title': item.get('title', ''),
                        'external_url': item['external_url']}
                    if not item['published']:
                        built_item['published'] = False
                else:
                    logging.warn("I can't find the module item "
                            f"'{item['title']}' locally and I couldn't figure "
                            "out how to pull it because it is not an "
                            "easel-supported type: " + item['type'])
                    continue

            position = item.get('position', 0)
            if position not in items:
                items[position] = []
            if icid:
                built_item = {"item": icid.filename, "indent": item.get('indent', 0)}
                if item['type'] == 'File' and 'title' in item:
                    built_item['title'] = item['title']
            if 'indent' in built_item and built_item['indent'] == 0:
                del built_item['indent']
            items[position].append(built_item)

        # order items by position
        all_items = []
        for position in sorted(items.keys()):
            if position == 0:
                # we used 0 as default above so skip that for now
                continue
            all_items += items[position]
        # add positionless items to the end
        module_['items'] = all_items + items.get(0, [])
        modules.append(Module.build(module_))
    return modules
