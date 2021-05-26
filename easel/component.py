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

    def push(self, db, path, courses, path_args=[]):
        """path_args should be a list of arguments to format into the path
            - e.g., a component's canvas id for updating the component"""
        if not courses:
            courses = course.find_all(db)
        resps = []
        for course_ in courses:
            print(f"pushing {self} to {course_.name} ({course_.canvas_id})")
            path_args = [course_.canvas_id] + path_args
            resp = helpers.post(path.format(*path_args), self)
            resps.append(resp)
        return resps

    def create(self, db, courses):
        resps = self.push(db, self.create_path, courses)
        ids = {}
        for r in resps:
            if 'course_id' in r and 'id' in r:
                ids[r['course_id']] = r['id']
            else:
                print("TODO: handle unexpected response")
        self.canvas_ids = ids
        self.save(db)

    def update(self, db, courses):
        # TODO: how to have path_args for each course (for using the canvas_id
        # of the component for each course)? probably need to combine create
        # and update back into single push method, or remove push method
        # altogether with just create and update methods. Or reverse it: call
        # push and then the push method decides to create or update?
        self.push(db, self.update_path, courses, [self.canvas_id])
