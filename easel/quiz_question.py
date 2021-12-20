from easel import component
from easel import canvas_id
from easel import helpers
from easel import helpers_yaml
from easel import quiz

QUIZ_QUESTIONS_PATH=quiz.QUIZ_PATH+"/questions"
QUIZ_QUESTION_PATH=QUIZ_QUESTIONS_PATH+"/{}"
QUIZ_QUESTIONS_TABLE="quiz_questions"
WRAPPER="question"
VALID_TYPES = ["calculated_question", "essay_question", "file_upload_question",
        "fill_in_multiple_blanks_question", "matching_question",
        "multiple_answers_question", "multiple_choice_question",
        "multiple_dropdowns_question", "numerical_question",
        "short_answer_question", "text_only_question", "true_false_question"]

class QuizQuestion(component.Component):

    def __init__(self, question_name=None, question_text=None,
            quiz_group_id=None, question_type=None, position=None,
            points_possible=None, correct_comments=None,
            incorrect_comments=None, neutral_comments=None,
            matching_answer_incorrect_matches=None, formulas=None,
            variables=None, text_after_answers=None, answers=[],
            id=None, filename=""):
        super().__init__(create_path=QUIZ_QUESTIONS_PATH,
                update_path=QUIZ_QUESTION_PATH, db_table=QUIZ_QUESTIONS_TABLE,
                canvas_wrapper=WRAPPER, filename=filename)
        self.question_name=question_name
        if question_text:
            question_text = question_text.strip()
            question_html = helpers.md2html(question_text)
            # TODO
            # python-markdown does not support attribute lists on tables but
            # the default table in canvas is hard to read. This solves that as
            # long as we always want the same formatting on tables.
            self.question_text = question_html.replace("<table>", "<table class=\"table table-striped table-bordered\">")
        else:
            self.question_text = None
        self.id = id
        self.quiz_group_id=quiz_group_id
        self.question_type=question_type
        self.position=position
        self.points_possible=points_possible
        self.correct_comments=correct_comments
        self.incorrect_comments=incorrect_comments
        self.neutral_comments=neutral_comments
        self.matching_answer_incorrect_matches=matching_answer_incorrect_matches
        self.variables=variables
        self.formulas=formulas
        self.text_after_answers=text_after_answers
        self.answers=answers
        for answer in self.answers:
            if 'answer_text' in answer:
                answer_text = answer.get("answer_text", "")
                if answer_text and isinstance(answer_text, str):
                    answer["answer_text"] = answer_text.replace('\n', ' ').strip()
            if 'answer_html' in answer:
                answer['answer_html'] = helpers.md2html(answer['answer_html'])
            if 'comments_html' in answer:
                answer['comments_html'] = helpers.md2html(answer['comments_html'])

    def __eq__(self, other):
        return (self.id == other.id and
                self.question_name == other.question_name and
                self.question_text == other.question_text)

    def __iter__(self):
        # canvas expects a list of answers to be in the form of an answers
        # object where it's children keys are index numbers and the values are
        # the actual answer objects
        question = dict(super().__iter__())
        new_answers = {}
        for i in range(len(question["question"]["answers"])):
            new_answers[str(i)] = question["question"]["answers"][i]
        # TODO: for formula questions to work, probably need to reformat the
        # self.formulas and self.variables lists in the same way as the answers
        question["question"]["answers"] = new_answers
        for key in question:
            yield (key, question[key])

    def __repr__(self):
        return f"QuizQuestion(id={self.id}, question_name={self.question_name}, " \
                f"question_type={self.question_type}, " \
                f"points_possible={self.points_possible}, "\
                f"answers_count={len(self.answers)})"

    def md(self):
        out = self.question_text
        for answer in self.answers:
            for key in ['answer_html', 'answer_text']:
                if key in answer:
                    out += "\n- A: " + answer[key]
        return out

    def format_create_path(self, db, *path_args):
        """2 args -> course_id, quiz_id"""
        course_id = path_args[0]
        cid = canvas_id.CanvasID(path_args[1].filename, course_id)
        cid.find_id(db)
        return self.create_path.format(course_id, cid.canvas_id)

    def format_update_path(self, db, *path_args):
        """3 args -> course_id, quiz_id, quiz_question_id"""
        course_id = path_args[0]
        cid = canvas_id.CanvasID(path_args[2].filename, course_id)
        cid.find_id(db)
        return self.update_path.format(course_id, cid.canvas_id, path_args[1])

# Needed for custom yaml tag
def constructor(loader, node):
    return helpers_yaml.construct_node(loader, node, QuizQuestion)
