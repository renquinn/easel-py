from easel import component
from easel import course

GRADING_SCHEME_PATH=course.COURSE_PATH+"/grading_standards"
GRADING_SCHEME_TABLE="grading_scheme"

class GradingScheme(component.Component):

    def __init__(self, title="Default Grading Scheme", grading_scheme_entry={},
            filename="grading_scheme.yaml"):
        super().__init__(create_path=GRADING_SCHEME_PATH,
                update_path=GRADING_SCHEME_PATH+"/{}",
                db_table=GRADING_SCHEME_TABLE, filename=filename)
        self.title = title
        self.grading_scheme_entry = grading_scheme_entry

    def __repr__(self):
        return f"GradingScheme(title={self.title}, grading_scheme_entry={self.grading_scheme_entry})"

# Needed for custom yaml tag
def constructor(loader, node):
    return GradingScheme(**loader.construct_mapping(node))
