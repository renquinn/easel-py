import logging
from easel import course
from easel import helpers

class Component:

    def __init__(self, create_path, update_path, db_table=""):
        """assumes paths require course id"""
        self.create_path = create_path
        self.update_path = update_path
        self.table = db_table

    def __iter__(self):
        fields = vars(self).copy()
        fields.pop("create_path", None)
        fields.pop("update_path", None)
        fields.pop("table", None)
        for field in fields.items():
            if field[0] not in ["canvas_ids"] and field[1] is not None:
                yield field

    def find(self, db):
        table = db.table(self.table)
        return table.search(self.gen_query())

    def gen_query(self):
        raise NotImplementedError

    def save(self, db):
        c = dict(self)
        c['canvas_ids'] = self.canvas_ids
        table = db.table(self.table)
        table.upsert(c, self.gen_query())

    def push(self, db, course_, dry_run):
        found = self.find(db)
        if not found:
            # create
            path = self.create_path.format(course_.canvas_id)
            resp = helpers.post(path, self, dry_run=dry_run)
            if dry_run:
                print("DRYRUN - grabbing the canvas_id and saving it on"
                        " the component (assuming the request worked)")
                return
            if 'id' in resp:
                self.canvas_ids[course_.canvas_id] = resp['id']
                self.save(db)
            else:
                print("TODO: handle unexpected response when creating component")
                print(resp)
                return
        else:
            # update
            if len(found) > 1:
                print("TODO: handle too many results")
                return
            found = build(type(self).__name__, dict(found[0]))
            found.merge(self)
            course_id = str(course_.canvas_id)
            if course_id not in found.canvas_ids:
                print(f"failed to push {found} to course {course_}")
                print(f"no canvas id found for this component on that course")
                return
            path = found.update_path.format(course_id,
                    found.canvas_ids[course_id])
            resp = helpers.put(path, found, dry_run=dry_run)
            # TODO: check resp. only save updates if good?
            if dry_run:
                print("DRYRUN - saving the component")
            else:
                found.save(db)

    def merge(self, other):
        # TODO: include some sort of confirmation prompt? or maybe that's what
        # --dry-run is for (it could print the fields to be merged)?
        for k, v in other.__iter__():
            # TODO: make sure we aren't overriding important metadata (e.g., canvas_ids)
            logging.info(f"self.{k} = {getattr(self, k)} -> other.{k} = {v}")
            setattr(self, k, v)

from easel import assignment_group
def build(class_name, dictionary):
    components = {"AssignmentGroup": assignment_group.AssignmentGroup}
    return components[class_name](**dictionary)
