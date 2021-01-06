from easel import course
from easel import helpers

class Component:

    def __init__(self, path, path_args=[]):
        """assumes path requires course id, path_args are for anything else"""
        self.path = path
        self.path_args = path_args

    def __iter__(self):
        fields = vars(self).copy()
        fields.pop("path", None)
        fields.pop("path_args", None)
        keys = list(fields.keys())
        for key in keys:
            if fields[key] is None:
                del fields[key]
        yield from fields.items()

    def push(self, db, courses):
        if not courses:
            courses = course.find_all(db)
        for course_ in courses:
            print(f"pushing {self} to {course_.name} ({course_.canvas_id})")
            path_args = [course_.canvas_id] + self.path_args
            helpers.post(self.path.format(*path_args), self)
