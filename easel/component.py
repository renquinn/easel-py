from easel import course
from easel import helpers

class Component:

    def __init__(self, create_path, update_path):
        """assumes paths require course id"""
        self.create_path = create_path
        self.update_path = update_path

    def __iter__(self):
        fields = vars(self).copy()
        fields.pop("create_path", None)
        fields.pop("update_path", None)
        fields.pop("table", None)
        for field in fields.items():
            if field[0] not in ["canvas_ids"] and field[1] is not None:
                yield field

    def find(self, db):
        return db.search(self.gen_query())

    def gen_query(self):
        raise NotImplementedError

    def save(self, db):
        c = dict(self)
        table = db.table(self.table)
        table.upsert(c, self.gen_query())

    def push(self, db, course_):
        found = self.find(db)
        if not found:
            # create
            path = self.create_path.format(course_.canvas_id)
            resp = helpers.post(path, self)
            # TODO: what does resp look like? assuming for now that it's the
            # component as saved in canvas
            if 'course_id' in resp and 'id' in resp:
                self.canvas_ids[resp['course_id']] = resp['id']
                # TODO: any other metadata we should grab from the response?
                self.save(db)
            else:
                print("TODO: handle unexpected response when creating component")
                print(resp)
                return
        else:
            # update
            # TODO: found might be a list, but it should have 1 item in it if so
            # changes in the md file (self) should be merged into the db record
            found.merge(self)
            if course_.canvas_id not in found.canvas_ids:
                print(f"failed to push {found} to course {course_.name}")
                print(f"no canvas id found for this component on that course")
                return
            path = found.update_path.format(course_.canvas_id,
                    found.canvas_ids[course_.canvas_id])
            resp = helpers.put(path, found)
            # TODO: check resp. only save updates if good?
            found.save(db)

    def merge(self, other):
        # TODO: include some sort of confirmation prompt? or maybe that's what
        # --dry-run is for (it could print the fields to be merged)?
        for k, v in super(Component, other).__iter__:
            # TODO: make sure we aren't overriding important metadata (e.g., canvas_ids)
            setattr(self, k, v)
