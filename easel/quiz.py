import logging
import random
import tinydb

from easel import assignment_group
from easel import canvas_id
from easel import component
from easel import course
from easel import helpers
from easel import helpers_yaml

QUIZZES_PATH=course.COURSE_PATH+"/quizzes"
QUIZ_PATH=QUIZZES_PATH+"/{}"
QUIZZES_TABLE="quizzes"
WRAPPER="quiz"

class Quiz(component.Component):

    def __init__(self, title=None, published=None, description=None,
            points_possible=None, allowed_attempts=None, due_at=None,
            unlock_at=None, lock_at=None, quiz_type=None, time_limit=None,
            shuffle_answers=None, hide_results=None, show_correct_answers=None,
            show_correct_answers_last_attempt=None,
            show_correct_answers_at=None, hide_correct_answers_at=None,
            scoring_policy=None, one_question_at_a_time=None,
            cant_go_back=None, access_code=None, ip_filter=None,
            one_time_results=None, only_visible_to_overrides=None,
            anonymous_submissions=None, assignment_group_id=None,
            remember_published=None,
            quiz_questions=None, assignment_group=None, filename=""):
        super().__init__(create_path=QUIZZES_PATH,
                update_path=QUIZ_PATH, db_table=QUIZZES_TABLE,
                canvas_wrapper=WRAPPER, filename=filename)
        self.title=title
        self.published=published
        self.remember_published=published # see the end of the postprocess method
        self.description=description
        self.points_possible=points_possible
        self.allowed_attempts=allowed_attempts
        self.due_at=due_at
        self.unlock_at=unlock_at
        self.lock_at=lock_at
        self.quiz_type=quiz_type
        self.time_limit=time_limit
        self.shuffle_answers=shuffle_answers
        self.hide_results=hide_results
        self.show_correct_answers=show_correct_answers
        self.show_correct_answers_last_attempt=show_correct_answers_last_attempt
        self.show_correct_answers_at=show_correct_answers_at
        self.hide_correct_answers_at=hide_correct_answers_at
        self.scoring_policy=scoring_policy
        self.one_question_at_a_time=one_question_at_a_time
        self.cant_go_back=cant_go_back
        self.access_code=access_code
        self.ip_filter=ip_filter
        self.one_time_results=one_time_results
        self.only_visible_to_overrides=only_visible_to_overrides
        self.anonymous_submissions=anonymous_submissions
        self.assignment_group_id=assignment_group_id
        if description:
            self.description = helpers.md2html(description.strip())
        else:
            self.description = None
        # easel-managed attrs
        # local variable has to be called assignment_group (clashes with module
        # title) to match the yaml and Canvas response
        self.assignment_group = assignment_group
        # quiz_questions can only be pushed after the quiz is created (postprocess)
        self.quiz_questions = quiz_questions

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
         self.remember_published = self.published
         self.published = False

    def postprocess(self, db, course_, dry_run):
        course_id = course_.canvas_id
        cid = canvas_id.CanvasID(self.filename, course_id)
        cid.find_id(db)
        if not cid.canvas_id:
            print(f"failed to add QuizQuestions to {self}, we don't "
                    "have a canvas id for it")
            print("make sure the quiz has first been pushed to Canvas")
            return

        # delete any existing questions on the quiz
        # we'll use the local file as the source of truth and always update
        # canvas to match it
        quiz_path = QUIZ_PATH.format(course_id, cid.canvas_id)
        questions_path = quiz_path + "/questions"
        quiz_questions = helpers.get(questions_path, dry_run)
        for question in quiz_questions:
            if 'id' in question:
                path = questions_path+"/{}".format(question['id'])
                helpers.delete(path)

        # prepare actual QuizQuestion objects to be pushed to canvas
        questions = build_questions(self.quiz_questions)

        # push the questions
        for question in questions:
            print(f"\tpushing {question} to Quiz {self}")
            question.push(db, course_, dry_run, parent_component=self)

        # once I push the questions, canvas doesn't seem to update the
        # quiz's points possible until I save the entire quiz again...
        # https://community.canvaslms.com/t5/Question-Forum/Saving-Quizzes-w-API/td-p/226406
        # turns out that canvas won't do this if the quiz is unpublished when
        # you create the questions. so I'm hackily unpublishing and then
        # publishing (if the user wants to publish it)
        if self.remember_published:
            helpers.put(quiz_path, {"quiz": {"published": True}})

    def __repr__(self):
        return f"Quiz(title={self.title}, published={self.published})"

QUESTION_ID_KEY='id'
def build_questions(quiz_questions):
    questions = []
    for qq in quiz_questions:
        if isinstance(qq, str):
            # just a string, assume it's a yaml file's path
            # open the yaml file and read it in directly
            # assume it contains 1 or more QuizQuestion definitions
            questions += load_questions_file(qq)
        elif isinstance(qq, dict):
            if 'bank' in qq:
                # assume they are referring to a quiz_questions file
                bank_questions = load_questions_file(qq['bank'])
                if QUESTION_ID_KEY in qq:
                    # grab question at that position in the file
                    # TODO: make sure we haven't already picked that
                    # question. for now maybe just encourage users to order
                    # the questions so that the randomized ones are last
                    qid = qq[QUESTION_ID_KEY]
                    found = None
                    for q in bank_questions:
                        if q.id and q.id == qid:
                            if found:
                                logging.warn("Already found a question with "
                                        f"the id {qid}. The ids in a file "
                                        "should be unique. For now we'll use "
                                        "the question with this id found last "
                                        "in the list.")
                            q.id = None
                            found = q
                    if found:
                        questions.append(found)
                    else:
                        logging.error("Failed to find a question with the id "
                                f"{qid} in the bank {qq['bank']}")
                else:
                    # they didn't specify a particular question so pick one
                    # at random from the file but make sure we haven't yet
                    # used that one
                    indexes = list(range(len(bank_questions)))
                    random.shuffle(indexes)
                    for i in indexes:
                        if bank_questions[i] not in questions:
                            questions.append(bank_questions[i])
                            break
                        # TODO: what if we've already used all of them?
            else:
                # assume they are directly specifying a question here
                from easel import quiz_question # import here to prevent circular import
                questions.append(quiz_question.QuizQuestion(**qq))
        else:
            raise TypeError(f"Invalid quiz question specification on Quiz {self}")
    return questions


def load_questions_file(filename):
    # I don't want to require users to put a single question in a list so we
    # detect if it's a list and if not, put it in a list
    contents = helpers_yaml.read(filename)
    if not isinstance(contents, list):
        contents = [contents]
    return contents

# Needed for custom yaml tag
def constructor(loader, node):
    return Quiz(**loader.construct_mapping(node))
