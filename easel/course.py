import os
import urllib.parse
import sys
import tinydb

from easel import helpers

COURSES_PATH=helpers.API+"/courses"
COURSE_PATH=COURSES_PATH+"/{}"
COURSES_TABLE='courses'
SYLLABUS_FILE="syllabus.md"

class Course:

    def __init__(self, canvas_id=-1, name="", code="", workflow_state="", syllabus=""):
        self.canvas_id = canvas_id
        self.name = name
        self.code = code
        self.workflow_state = workflow_state
        self.syllabus = helpers.filter_canvas_html(syllabus)
        if self.syllabus is None:
            self.syllabus = ""

    def __repr__(self):
        return (f"Course(canvas_id={self.canvas_id}, name={self.name}, "
                "code={self.code})")

    def __str__(self):
        return f"{self.canvas_id}\t{self.name}\t{self.code}\t{self.workflow_state}"

    def save(self, db):
        # db
        c = dict(vars(self))
        del c["syllabus"]
        courses = db.table(COURSES_TABLE)
        courses.insert(c)
        # syllabus file
        if not os.path.isfile(SYLLABUS_FILE):
            with open(SYLLABUS_FILE, "w") as f:
                f.write(self.syllabus)

    def remove(self, db):
        courses = db.table(COURSES_TABLE)
        CourseQ = tinydb.Query()
        courses.remove(CourseQ.name == self.name)

def build(cdict):
    return Course(cdict["canvas_id"], cdict["name"], cdict["code"],
            cdict["workflow_state"], cdict.get("syllabus", ""))

def find(db, course_id):
    courses = db.table(COURSES_TABLE)
    CourseQ = tinydb.Query()
    return [build(c) for c in courses.search(CourseQ.canvas_id == course_id)]

def find_all(db):
    return [build(c) for c in db.table(COURSES_TABLE).all()]

def get_id_from_url(course_url):
    try:
        parsed = urllib.parse.urlparse(course_url)
        path = parsed.path.split("/")
        courseId = int(path[len(path)-1])
        return courseId
    except ValueError:
        print(f"Invalid course url f{course_url}")
        sys.exit(1)

def match_courses(db, terms):
    courses = []
    for course_ in terms:
        courses += match_course(db, course_)
    for course_ in courses:
        print(course_)
    # TODO: is it worth confirming? maybe only confirm if the length of the
    # returned courses differs from the length of the search terms list
    response = input("Found these courses. Correct? (y/n) ")
    if response.lower() == 'n':
        print("Please refine your search terms")
        sys.exit()
    return courses

def match_course(db, search):
    # assume searching by canvas id first
    if search.isdigit():
        results = find(db, int(search))
        if len(results) > 0:
            return results

    # if we didn't find the course, user might have given the section number
    # so search for it by name
    results = []
    for term in search.split(" "):
        test_func = lambda field: term in field
        CourseQ = tinydb.Query()
        courses = db.table(COURSES_TABLE)
        results += [build(c) for c in courses.search(CourseQ.code.test(test_func))]
    return results

def pull(db, course_id):
    params = {"include[]": "syllabus_body"}
    response = helpers.get(COURSE_PATH.format(course_id), params=params)
    response["canvas_id"] = response["id"]
    return Course(response["id"], response["name"], response["course_code"],
            response["workflow_state"], response["syllabus_body"])

def push_syllabus(db, course_id, dry_run):
    with open("syllabus.md") as f:
        c = {"course": {
            "syllabus_body": helpers.md2html(f.read()),
            "apply_assignment_group_weights": True
            }}
        if dry_run:
            print(f"DRYRUN - pushing syllabus")
        else:
            helpers.put(COURSE_PATH.format(course_id), c)
