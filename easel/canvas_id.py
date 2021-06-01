import tinydb

TABLE="canvas_ids"

class CanvasID:

    def __init__(self, filename="", course_id="", canvas_id=""):
        self.filename = filename
        self.course_id = course_id
        self.canvas_id = canvas_id

    def __repr__(self):
        return f"CanvasID(filename={self.filename}, course_id={self.course_id}, canvas_id={self.canvas_id})"

    def find_id(self, db):
        """search for a component's canvas id using its filename and course,
        None if not found"""
        table = db.table(TABLE)
        results = table.search(self.gen_query())
        # assume a component will only have a single canvas_id per course
        if len(results) > 0:
            self.canvas_id = results[0]['canvas_id']

    def gen_query(self):
        CID = tinydb.Query()
        return (CID.filename == self.filename) & (CID.course_id == self.course_id)

    def save(self, db):
        table = db.table(TABLE)
        table.upsert(vars(self), self.gen_query())

    def remove(self, db):
        table = db.table(TABLE)
        table.remove(self.gen_query())
