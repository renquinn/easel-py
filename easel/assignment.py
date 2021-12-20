import json
import tinydb
from tqdm import tqdm

from easel import assignment_group
from easel import canvas_id
from easel import component
from easel import course
from easel import helpers
from easel import helpers_yaml

ASSIGNMENTS_PATH=course.COURSE_PATH+"/assignments"
ASSIGNMENT_PATH=ASSIGNMENTS_PATH+"/{}"
ASSIGNMENTS_TABLE="assignments"
WRAPPER="assignment"
ASSIGNMENTS_DIR="assignments"

class Assignment(component.Component):

    def __init__(self, name=None, published=None, grading_type=None,
            points_possible=None, submission_types=None,
            allowed_extensions=None, external_tool_tag_attributes=None,
            allowed_attempts=None, due_at=None, unlock_at=None, lock_at=None,
            peer_reviews=None, automatic_peer_reviews=None,
            peer_reviews_assign_at=None, intra_group_peer_reviews=None,
            anonymous_submissions=None, omit_from_final_grade=None,
            use_rubric_for_grading=None, assignment_group_id=None,
            grade_group_students_individually=None, rubric=None,
            rubric_settings=None, position=None, description=None,
            free_form_criterion_comments=None, assignment_group=None,
            notify_of_update=None,
            filename=""):
        super().__init__(create_path=ASSIGNMENTS_PATH,
                update_path=ASSIGNMENT_PATH, db_table=ASSIGNMENTS_TABLE,
                canvas_wrapper=WRAPPER, filename=filename)
        self.allowed_attempts = allowed_attempts
        self.allowed_extensions = allowed_extensions
        self.anonymous_submissions = anonymous_submissions
        self.assignment_group_id = assignment_group_id
        self.automatic_peer_reviews = automatic_peer_reviews
        self.due_at = due_at
        self.external_tool_tag_attributes = external_tool_tag_attributes
        self.free_form_criterion_comments = free_form_criterion_comments
        self.grade_group_students_individually = grade_group_students_individually
        self.grading_type = grading_type
        self.intra_group_peer_reviews = intra_group_peer_reviews
        self.lock_at = lock_at
        self.name = name
        self.omit_from_final_grade = omit_from_final_grade
        self.peer_reviews = peer_reviews
        self.peer_reviews_assign_at = peer_reviews_assign_at
        self.points_possible = points_possible
        self.position = position
        self.published = published
        self.rubric = rubric
        self.rubric_settings = rubric_settings
        self.submission_types = submission_types
        self.unlock_at = unlock_at
        self.use_rubric_for_grading = use_rubric_for_grading
        if description:
            self.description = helpers.md2html(description.strip())
        else:
            self.description = description
        self.notify_of_update = notify_of_update
        # easel-managed attrs
        # local variable has to be called assignment_group (clashes with module
        # name) to match the yaml and Canvas response
        self.assignment_group = assignment_group

    def get_assignment_group_id(self, db, course_id):
        if self.assignment_group:
            ags = db.table(assignment_group.ASSIGN_GROUPS_TABLE)
            results = ags.search(tinydb.Query().name == self.assignment_group)
            if not results:
                raise ValueError(f"failed to find AssignmentGroup called '{self.assignment_group}'")
            # assumes assignment group names will be unique
            fname = assignment_group.AssignmentGroup(**dict(results[0])).filename
            cid = canvas_id.CanvasID(fname, course_id)
            cid.find_id(db)
            self.assignment_group_id = cid.canvas_id

    def preprocess(self, db, course_, dry_run):
         self.get_assignment_group_id(db, course_.canvas_id)

    def __repr__(self):
        return f"Assignment(name={self.name}, published={self.published})"

    @classmethod
    def build(cls, fields):
        extras = ['id', 'assignment_group_id', 'created_at', 'updated_at',
                'has_overrides', 'all_dates', 'course_id', 'html_url',
                'submission_download_url', 'due_date_required',
                'max_name_length', 'turnitin_enabled', 'vericite_enabled',
                'turnitin_settings', 'peer_review_count', 'group_category_id',
                'needs_grading_count', 'needs_grading_count_by_section',
                'post_to_sis', 'integration_id', 'integration_data',
                'has_submitted_submissions', 'grading_standard_id',
                'unpublishable', 'only_visible_to_overrides',
                'locked_for_user', 'lock_info', 'lock_explanation', 'quiz_id',
                'discussion_topic', 'freeze_on_copy', 'frozen',
                'frozen_attributes', 'submission', 'assignment_visibility',
                'overrides', 'moderated_grading', 'grader_count',
                'final_grader_id', 'grader_comments_visible_to_graders',
                'graders_anonymous_to_graders',
                'grader_names_visible_to_final_grader', 'anonymous_grading',
                'post_manually', 'score_statistics', 'can_submit',
                "workflow_state", "submissions_download_url", "url",
                "sis_assignment_id", "secure_params",
                "require_lockdown_browser", "original_assignment_name",
                "original_course_id", "original_quiz_id",
                "original_assignment_id", "muted", "is_quiz_assignment",
                "in_closed_grading_period", "external_tool_tag_attributes",
                "can_duplicate", "anonymous_peer_reviews",
                "anonymous_instructor_annotations", "anonymize_students",
                "important_dates"]
        defaults = [("automatic_peer_reviews", False),
                ("grade_group_students_individually", False),
                ("intra_group_peer_reviews", False),
                ("omit_from_final_grade", False),
                ("peer_reviews", False)]
        component.filter_fields(fields, extras, defaults)
        if 'description' in fields:
            fields['description'] = helpers.filter_canvas_html(fields['description'])
        return Assignment(**fields)


# Needed for custom yaml tag
def constructor(loader, node):
    return Assignment(**loader.construct_mapping(node))

def pull(db, course_, assignment_id, dry_run):
    course_id = course_.canvas_id
    a = helpers.get(ASSIGNMENT_PATH.format(course_id,
        assignment_id), dry_run=dry_run)
    if not a.get('id'):
        logging.error(f"Assignment {assignment_id} does not exist for course {course_id}")
        return None, None
    cid = canvas_id.find_by_id(db, course_id, a.get('id'))
    if cid:
        a['filename'] = cid.filename
    else:
        a['filename'] = component.gen_filename(ASSIGNMENTS_DIR, a.get('name',''))
        cid = canvas_id.CanvasID(a['filename'], course_id)
        cid.canvas_id = a.get('id')
        cid.save(db)

    # check assignment_group_id to fill in assignment_group by name
    agid = a.get('assignment_group_id')
    if agid:
        # first check if we have a cid for the assignment group
        agcid = canvas_id.find_by_id(db, course_id, agid)
        if agcid:
            ag = helpers_yaml.read(agcid.filename)
            if ag:
                a['assignment_group'] = ag.name
            else:
                logging.error("failed to find the assignment group for "
                        f"the assignment group with id {agid}. Your "
                        ".easeldb may be out of sync")
        else:
            # we could look at all the local assignment group files if we
            # don't have a cid for it but chances are there isn't a file.
            # so might as well just go back to canvas and ask for it
            agpath = assignment_group.ASSIGN_GROUP_PATH.format(course_id, agid)
            r = helpers.get(agpath, dry_run=dry_run)
            if 'name' in r:
                a['assignment_group'] = r['name']
            else:
                logging.error("TODO: invalid response from canvas for "
                        "the assignment group: " + json.dumps(r, indent=4))

    return Assignment.build(a), cid

def pull_all(db, course_, dry_run):
    r = helpers.get(ASSIGNMENTS_PATH.format(course_.canvas_id),
            dry_run=dry_run)
    assignments = []
    print("pulling assignment contents")
    for assignment in tqdm(r):
        # skip quizzes (handle in quiz.py)
        if assignment.get("is_quiz_assignment"):
            continue

        assignment_, _ = pull(db, course_, assignment.get('id'), dry_run)
        if assignment_:
            assignments.append(assignment_)
    return assignments
