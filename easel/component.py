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
    - [optional] a postprocess() method to resolve any easel-managed info to
      canvas info, but those that require the canvas item to be create first
      (e.g., adding module items to a module without keeping track of a
      separate file for module items)
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

    def format_create_path(self, db, *path_args):
        """default: 1 arg -> course_id"""
        return self.create_path.format(*path_args)

    def format_update_path(self, db, *path_args):
        """default: 2 args -> course_id, component_id"""
        return self.update_path.format(*path_args)

    def find(self, db):
        table = db.table(self.table)
        return table.search(self.gen_query())

    def get_canvas_id(self, db, course_id):
        cid = canvas_id.CanvasID(self.filename, course_id)
        cid.find_id(db)
        return cid.canvas_id

    def gen_query(self):
        return tinydb.Query().filename == self.filename

    def preprocess(self, db, course_, dry_run):
        pass

    def postprocess(self, db, course_, dry_run):
        pass

    def remove(self, db, course_, dry_run):
        course_id = course_.canvas_id
        cid = canvas_id.CanvasID(self.filename, course_id)
        cid.find_id(db)
        if not cid.canvas_id:
            print(f"Failed to delete {self} from course {course_}")
            print("No canvas information found for the given component. If the"
                    " component still exists in Canvas we may have lost track "
                    "of it so you will have to manually delete it. Sorry!")
            return

        # TODO: confirm they want to delete it?
        path = self.format_update_path(db, course_id, cid.canvas_id)
        resp = helpers.delete(path, dry_run=dry_run)
        err = False
        if "errors" in resp:
            print(f"Canvas failed to delete the component {self}")
            for error in resp['errors']:
                if "does not exist" in error['message']:
                    print("But that's ok because you were probably just "
                            "removing the local canvas info for it.")
                else:
                    print("CANVAS ERROR:", error['message'])
                    err = True
        if err:
            print("Local remove action aborted")
            print("Canvas may or may not have successfully deleted the component")
            return

        if dry_run:
            print(f"DRYRUN - deleting the canvas relationship for {self}")
        else:
            cid.remove(db)
            # delete any child elements (e.g., module items)
            # filename format for nested child objects is
            # {parent_filename}--{child_identifier}
            children = canvas_id.find_by_prefix(db, course_id, cid.filename+"--")
            for child in children:
                child.remove(db)

    def save(self, db):
        c = dict(self.gen_fields())
        c['filename'] = self.filename
        table = db.table(self.table)
        table.upsert(c, self.gen_query())

    def push(self, db, course_, dry_run, parent_component=None):
        """
        push the component to the given canvas course

        The parent_component is used for the more complex scenarios when canvas
        nests components inside of others (e.g., ModuleItems inside of
        Modules). Usually in these cases, the child component's API endpoint
        paths will be an extension of the parent's path, so it parent_component
        allows us to extend the default behavior. In these cases, push() will
        be called in a different location than the typical execution path in
        commands.py. However, this other location should mimic that typical
        behavior (see preprocess() in module.py).
        """
        course_id = course_.canvas_id
        found = self.find(db)
        cid = canvas_id.CanvasID(self.filename, course_id)
        cid.find_id(db)

        # possible scenarios:
        #   - record not found, no canvas id -> create
        #   - record found, no canvas id -> yaml overrules record, right?
        #       that's what it's doing now -> create
        #   - record not found, canvas id found -> this one's weird.. should we
        #       pull the canvas version and merge with the local version? right
        #       now it just overwrites the canvas version -> update
        #   - record found, canvas id found -> update
        #   - TODO: what about if we have a canvas id but the component has
        #       been deleted in canvas? maybe just delete the canvas id record
        #       and try again? Since deleting components might be rare anyway,
        #       for now we'll just inform the user and they can remove the
        #       component themselves before proceeding. This will mainly happen
        #       when we delete a component that tracks children (e.g., an
        #       assignment group because it will delete the
        #       assignments that belong to that group, a module with its items)
        #       so we might want to be proactive when we delete and then go
        #       delete the assignments, but that requires even deeper tracking
        #       ahead of time.
        # conclusion: whether we create or update only depends on the canvas id
        # but later on we might end up needing to do other stuff depending on
        # whether or not we have a db record?
        if cid.canvas_id == "":
            # create
            path = self.format_create_path(db, course_id, parent_component)
            self.preprocess(db, course_, dry_run)
            resp = helpers.post(path, self, dry_run=dry_run)

            if dry_run:
                print("DRYRUN - saving the canvas_id for the component "
                        "(assuming the request worked)")
                return

            if self.filename:
                # only save the canvas id if we have a filename because we
                # don't want to save some components (e.g., quiz questions)
                if 'id' in resp:
                    self.save(db)
                    cid.canvas_id = resp['id']
                    cid.save(db)
                elif 'url' in resp:
                    # pages use a url instead of an id but we can use them
                    # interchangably for this
                    self.save(db)
                    cid.canvas_id = resp['url']
                    cid.save(db)
                elif "message" in resp:
                    logging.error(resp['message'])
                else:
                    raise ValueError("TODO: handle unexpected response when creating component")

            self.postprocess(db, course_, dry_run)

        else:
            # update
            if not found:
                found = self
            elif len(found) > 1:
                raise ValueError("TODO: handle too many results, means the filename was not unique")
            else:
                found = build(type(self).__name__, dict(found[0]))
                found.merge(self)

            path = self.format_update_path(db, course_id, cid.canvas_id, parent_component)
            found.preprocess(db, course_, dry_run)
            resp = helpers.put(path, found, dry_run=dry_run)
            if "errors" in resp:
                print(f"failed to update the component {found}")
                for error in resp['errors']:
                    if isinstance(error, dict):
                        if "does not exist" in error['message']:
                            print("The component was deleted in canvas "
                                    "without us knowing about it. You should "
                                    "remove the component here and then try "
                                    "pushing it again.")
                        else:
                            print("CANVAS ERROR:", error['message'])
                    else:
                        print("CANVAS ERROR:", error)

            if dry_run:
                print(f"DRYRUN - saving the component {found}")
            else:
                found.save(db)

            found.postprocess(db, course_, dry_run)

    def merge(self, other):
        # TODO: include some sort of confirmation prompt? or maybe that's what
        # --dry-run is for (it could print the fields to be merged)?
        for k, v in other.gen_fields():
            if v != getattr(self, k):
                logging.info(f"self.{k} = {getattr(self, k)} -> other.{k} = {v}")
                setattr(self, k, v)

    def pull(self, db, course_, dry_run):
        cid = canvas_id.CanvasID(self.filename, course_.canvas_id)
        cid.find_id(db)
        path = self.format_update_path(db, course_.canvas_id, cid.canvas_id)
        resp = helpers.get(path, dry_run=dry_run)
        remote = self.__class__.build(resp)
        remote.filename = self.filename
        return remote

def build(class_name, dictionary):
    from easel import assignment_group
    from easel import assignment
    from easel import external_tool
    from easel import module
    from easel import module_item
    from easel import page
    from easel import quiz
    components = {
            "Assignment": assignment.Assignment,
            "AssignmentGroup": assignment_group.AssignmentGroup,
            "ExternalTool": external_tool.ExternalTool,
            "Module": module.Module,
            "ModuleItem": module_item.ModuleItem,
            "Page": page.Page,
            "Quiz": quiz.Quiz,
            }
    return components[class_name](**dictionary)

def gen_filename(dir_, name):
    return dir_+"/"+name.lower().replace(' ', '_').replace('/', '-')+".yaml"

def filter_fields(fields, extra_fields_to_remove=[], default_fields_to_remove=[]):
    '''
    This is used to preprocess the fields of a component as returned by canvas.
    The idea is to 1) get rid of fields that we don't care about, and 2) get
    rid of some default values that we don't want filling up our yaml files.

    - extra_fields_to_remove: a list of strings where each string is a key that
      is returned by canvas for a component but that component's easel class
      does not know how to handle it
    - default_fields_to_remove: a list of tuples where each tuple represents
      the default value of a field as (field_key, default_value)
    '''
    for k in extra_fields_to_remove:
        if k in fields:
            del fields[k]

    for f in default_fields_to_remove:
        if f[0] in fields and fields[f[0]] == f[1]:
            del fields[f[0]]
