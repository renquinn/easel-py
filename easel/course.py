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

def format_syllabus(db, course_id):
    with open("syllabus.md") as f:
        text = f.read()
    # format fields from three different sources into syllabus:

    # 1. fields from syllabus meta data
    md_fields = {}
    lines = text.split('\n')
    delimeter_count = lines.count('---')
    if delimeter_count > 1:
        # parse metadata
        end_metadata = lines.index('---', 2)
        metadata = '\n'.join(lines[1:end_metadata])
        text = '\n'.join(lines[end_metadata+1:])
        # convert metadata from yaml
        '''
        Example format:
        ---
        custom_fields:
            677659:
                meeting_time: MW 12:00-1:15 pm
                room: Smith 107
                final_exam: Dec 14, 11 am
            647101:
                meeting_time: MWF 11:00-11:50 pm
                room: Smith 107
                final_exam: Dec 12, 11 am
        ---
        '''
        import yaml
        md_fields = yaml.load(metadata)['custom_fields']
        if course_id in md_fields:
            # TODO: I'm not a fan of this way to organize fields for multiple
            # sections in the yaml (see example format above)
            md_fields = md_fields[course_id]

    # 2. course-specific fields
    course_fields = md_fields
    c = find(db, course_id)[0]
    # TODO: Canvas may change the format of these fields in the future
    course_fields['code'] = c.code[:7]
    course_fields['crn'] = c.name[-6:-1]
    course_fields['semester'] = ' '.join(c.name.split()[1:3])
    course_fields['course_id'] = course_id

    # 3. global fields
    fields = helpers.get_global_template_fields()
    fields.update(course_fields)
    return helpers.md2html(text, fields)

def push_syllabus(db, course_id, dry_run):
    formatted = format_syllabus(db, course_id)
    c = {"course": {
            "syllabus_body": formatted,
            "apply_assignment_group_weights": True
        }}
    if dry_run:
        print(f"DRYRUN - pushing syllabus")
        print(formatted)
    else:
        helpers.put(COURSE_PATH.format(course_id), c)

def update_grading_scheme(db, course_id, grading_scheme_id, dry_run):
    c = {
            "course": {
                "grading_standard_id": grading_scheme_id,
                "apply_assignment_group_weights": True
            }
        }
    if dry_run:
        print(f"DRYRUN - updating grading scheme {grading_scheme_id} for course {course_id}")
    else:
        helpers.put(COURSE_PATH.format(course_id), c)

def publish(course_id, dry_run):
    c = {"offer": True}
    if dry_run:
        print(f"DRYRUN - publishing course {course_id}")
    else:
        helpers.put(COURSE_PATH.format(course_id), c)
