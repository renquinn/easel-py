from easel import component
from easel import course
from easel import helpers

ASSIGNMENTS_PATH=course.COURSE_PATH+"/assignments"

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
            rubric_settings=None, position=None, description=None):
        component.Component.__init__(self, ASSIGNMENTS_PATH)
        self.name = name
        self.published = published
        self.grading_type = grading_type
        self.points_possible = points_possible
        self.submission_types = submission_types
        self.allowed_extensions = allowed_extensions
        self.external_tool_tag_attributes = external_tool_tag_attributes
        self.allowed_attempts = allowed_attempts
        self.due_at = due_at
        self.unlock_at = unlock_at
        self.lock_at = lock_at
        self.peer_reviews = peer_reviews
        self.automatic_peer_reviews = automatic_peer_reviews
        self.peer_reviews_assign_at = peer_reviews_assign_at
        self.intra_group_peer_reviews = intra_group_peer_reviews
        self.anonymous_submissions = anonymous_submissions
        self.omit_from_final_grade = omit_from_final_grade
        self.use_rubric_for_grading = use_rubric_for_grading
        self.assignment_group_id = assignment_group_id
        self.grade_group_students_individually = grade_group_students_individually
        self.rubric = rubric
        self.rubric_settings = rubric_settings
        self.position = position
        if description:
            self.description = helpers.md2html(description.strip())
        else:
            self.description = description

    def __iter__(self):
        fields = dict(super().__iter__())
        wrapped = {"assignment": fields}
        yield from wrapped.items()

    def __repr__(self):
        return f"Assignment(name={self.name}, published={self.published})"


# Needed for custom yaml tag
def constructor(loader, node):
    return Assignment(**loader.construct_mapping(node))
