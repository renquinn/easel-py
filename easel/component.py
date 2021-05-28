import logging
import tinydb

from easel import canvas_id
from easel import course
from easel import helpers

class Component:
    """
    canvas component subclass requirements:
    - init method named parameters should be the name of the field as defined
      by canvas. named parameters with default of None will be ignored in the
      canvas api requests
    - inherit from Component, must supply:
        - create path (as an extension of course.COURSE_PATH)
        - update path (templated for the canvas id to be formatted in)
        - component's filename
        - db table
        - [optional] canvas_wrapper (when the api requires component fields to
          be wrapped in a single object)
    - add the component's class to the build function at the bottom of this file
    - [optional] a preprocess() method to resolve any easel-managed info to
      canvas info (e.g., assignment group name to canvas id)
    - [optional] a repr method is nice
    """

    def __init__(self, create_path="", update_path="", db_table="",
            canvas_wrapper="", filename=""):
        self.create_path = create_path
        self.update_path = update_path
        self.table = db_table
        self.canvas_wrapper = canvas_wrapper
        self.filename = filename

    def __iter__(self):
        if self.canvas_wrapper:
            fields = dict(self.gen_fields())
            wrapped = {self.canvas_wrapper: fields}
            yield from wrapped.items()
        else:
            for field in self.gen_fields():
                yield field

    def gen_fields(self):
        ignore_these = ["create_path", "update_path", "table",
                "canvas_wrapper", "filename"]
        fields = vars(self)
        for field in fields.items():
            if field[0] not in ignore_these and field[1] is not None:
                yield field

    def find(self, db):
        table = db.table(self.table)
        return table.search(self.gen_query())

    def gen_query(self):
        return tinydb.Query().filename == self.filename

    def preprocess(self, db, course_id):
        pass

    def save(self, db):
        c = dict(self.gen_fields())
        c['filename'] = self.filename
        table = db.table(self.table)
        table.upsert(c, self.gen_query())

    def push(self, db, course_, dry_run):
        course_id = course_.canvas_id
        found = self.find(db)
        if not found:
            # create
            path = self.create_path.format(course_id)
            self.preprocess(db, course_id)
            resp = helpers.post(path, self, dry_run=dry_run)
            if dry_run:
                print("DRYRUN - grabbing the canvas_id and saving it on"
                        " the component (assuming the request worked)")
                return
            if 'id' in resp:
                self.save(db)
                cid = canvas_id.CanvasID(self.filename, course_id, resp['id'])
                cid.save(db)
            elif 'url' in resp:
                # pages use a url instead of an id but we can use them
                # interchangably for this
                self.save(db)
                cid = canvas_id.CanvasID(self.filename, course_id, resp['url'])
                cid.save(db)
            else:
                raise ValueError("TODO: handle unexpected response when creating component")
        else:
            # update
            if len(found) > 1:
                raise ValueError("TODO: handle too many results, means the filename was not unique")
            found = build(type(self).__name__, dict(found[0]))
            found.merge(self)
            cid = canvas_id.CanvasID(self.filename, course_id)
            cid.find_id(db)
            if cid.canvas_id == "":
                print(f"failed to push {found} to course {course_}")
                print(f"no canvas id found for this component on that course")
                return
            path = found.update_path.format(course_id, cid.canvas_id)
            found.preprocess(db, course_id)
            resp = helpers.put(path, found, dry_run=dry_run)
            # TODO: check resp. only save if update worked?
            if dry_run:
                print(f"DRYRUN - saving the component {found}")
            else:
                found.save(db)

    def merge(self, other):
        # TODO: include some sort of confirmation prompt? or maybe that's what
        # --dry-run is for (it could print the fields to be merged)?
        for k, v in other.gen_fields():
            if v != getattr(self, k):
                logging.info(f"self.{k} = {getattr(self, k)} -> other.{k} = {v}")
                setattr(self, k, v)

def build(class_name, dictionary):
    from easel import assignment_group
    from easel import assignment
    from easel import external_tool
    from easel import module
    from easel import page
    components = {
            "Assignment": assignment.Assignment,
            "AssignmentGroup": assignment_group.AssignmentGroup,
            "ExternalTool": external_tool.ExternalTool,
            "Module": module.Module,
            "Page": page.Page,
            }
    return components[class_name](**dictionary)
