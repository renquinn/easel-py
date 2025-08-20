import logging
import random
import tinydb
from tqdm import tqdm

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
QUIZZES_DIR="quizzes"

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
            remember_published=None,
            anonymous_submissions=None, assignment_group_id=None,
            quiz_questions=None, assignment_group=None, filename="",
            yaml_order=[]):
        super().__init__(create_path=QUIZZES_PATH,
                update_path=QUIZ_PATH, db_table=QUIZZES_TABLE,
                canvas_wrapper=WRAPPER, filename=filename,
                yaml_order=yaml_order)
        self.title=title
        self.published=published
        self.remember_published=None # see the end of the postprocess method
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
        self.description = description
        # easel-managed attrs
        # local variable has to be called assignment_group (clashes with module
        # title) to match the yaml and Canvas response
        self.assignment_group = assignment_group
        # quiz_questions can only be pushed after the quiz is created (postprocess)
        self.quiz_questions = quiz_questions

    def __repr__(self):
        return f"Quiz(title={self.title}, published={self.published})"

    @classmethod
    def build(cls, fields):
        defaults = {
                "quiz_type": "assignment",
                "allowed_attempts": -1,
                "scoring_policy": "keep_highest",
                "published": True,
                "anonymous_submissions": False,
                "show_correct_answers": True,
                "require_lockdown_browser_for_results": False,
                "require_lockdown_browser_monitor": False,
                "lockdown_browser_monitor_data": "",
                "one_time_results": False,
                "show_correct_answers_last_attempt": False,
                "hide_results": None,
                "time_limit": None,
                "access_code": None,
                "ip_filter": None,
                "show_correct_answers_at": None,
                "hide_correct_answers_at": None,
                "cant_go_back": False,
                "one_question_at_a_time": False,
                }
        desired_fields = cls.__init__.__code__.co_varnames[1:]
        component.filter_fields(fields, desired_fields, defaults)
        if 'description' in fields:
            fields['description'] = helpers.filter_canvas_html(fields['description'])

        qq_defaults = {
                "correct_comments": "",
                "incorrect_comments": "",
                "neutral_comments": '',
                "comments": '',
                'position': None,
                "variables": None,
                "formulas": None,
                "answer_tolerance": None,
                "formula_decimal_places": None,
                "matches": None,
                "matching_answer_incorrect_matches": None,
                "answers": [],
                }
        from easel import quiz_question # import here to prevent circular import
        qq_desired_fields = quiz_question.QuizQuestion.__init__.__code__.co_varnames[1:]
        all_qqfields = {}
        all_qafields = {}
        filtered_questions = []
        for qqfields in fields['quiz_questions']:
            component.filter_fields(qqfields, qq_desired_fields, qq_defaults)
            if 'id' in qqfields:
                del qqfields['id']
            if 'question_text' in qqfields:
                qqfields['question_text'] = helpers.filter_canvas_html(qqfields['question_text'])

            all_qqfields.update(qqfields)
            for answer in qqfields.get('answers', []):
                # let's not use component.filter_fields for quiz question
                # answers since they are staying as dictionaries and there
                # should be much less extra fields than fields to keep
                extra_fields = ['id', 'html', 'migration_id', 'comments_html',
                        'incorrect_comments_html', 'correct_comments_html']
                for field in extra_fields:
                    if field in answer:
                        del answer[field]
                if 'comments' in answer and not answer['comments']:
                    del answer['comments']

                # the field names for answers are different when you pull so we
                # need to fix that to be consistent with the required field
                # names for pushing
                answer_keys = {
                        "text": "answer_text",
                        "weight": "answer_weight",
                        "left": "answer_match_left",
                        "right": "answer_match_right",
                        "comments": "answer_comments",
                        }
                for answer_key in answer_keys:
                    if answer_key in answer:
                        correct_key = answer_keys[answer_key]
                        answer[correct_key] = answer[answer_key]
                        del answer[answer_key]
                all_qafields.update(answer)
        try:
            return Quiz(**fields)
        except:
            import json
            print(json.dumps(all_qqfields, indent=4))
            print(json.dumps(all_qafields, indent=4))
            raise ValueError

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

    def md(self, db, course_, include_questions=True):
        if not self.description:
            return ''
        fields = helpers.get_global_template_fields()
        course_fields = helpers.get_course_template_fields(db, course_)
        fields.update(course_fields)
        description_text = helpers.md2html(self.description.strip(), fields)
        if include_questions:
            question_texts = []
            from easel import quiz_question # import here to prevent circular import
            for question in self.quiz_questions:
                question_texts.append(quiz_question.QuizQuestion(**question).md(db, course_))
            questions_text = '\n\n'.join(question_texts)
            description_text += f'\n\n{questions_text}'
        return description_text

    def preprocess(self, db, course_, dry_run):
        if self.description:
            self.description = self.md(db, course_, False)
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

    def pull(self, db, course_, dry_run):
        cid = canvas_id.CanvasID(self.filename, course_.canvas_id)
        cid.find_id(db)
        quiz_fields = dict(self.gen_fields())
        quiz_fields['id'] = cid.canvas_id
        pulled, _ = pull(db, course_, quiz_fields, dry_run)
        return pulled

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
    fields = helpers_yaml.construct_ordered_mapping(loader, node)
    return Quiz(**fields)

def pull(db, course_, quiz_, dry_run):
    course_id = course_.canvas_id
    quiz_id = quiz_.get('id')
    if not quiz_id:
        logging.error(f"Quiz {quiz_id} does not exist for course {course_id}")
        return None, None

    cid = canvas_id.find_by_id(db, course_id, quiz_id)
    if cid:
        quiz_['filename'] = cid.filename
    else:
        quiz_['filename'] = component.gen_filename(QUIZZES_DIR, quiz_.get('title',''))
        cid = canvas_id.CanvasID(quiz_['filename'], course_id)
        cid.canvas_id = quiz_.get('id')
        cid.save(db)

    # check assignment_group_id to fill in assignment_group by name
    agid = quiz_.get('assignment_group_id')
    if agid:
        # first check if we have a cid for the assignment group
        agcid = canvas_id.find_by_id(db, course_id, agid)
        if agcid:
            ag = helpers_yaml.read(agcid.filename)
            if ag:
                quiz_['assignment_group'] = ag.name
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
                quiz_['assignment_group'] = r['name']
            else:
                logging.error("TODO: invalid response from canvas for "
                        "the assignment group: " + json.dumps(r, indent=4))

    # quiz questions
    quiz_questions_path=QUIZ_PATH.format(course_.canvas_id, quiz_id)+"/questions"
    quiz_questions = helpers.get(quiz_questions_path)
    quiz_['quiz_questions'] = quiz_questions

    return Quiz.build(quiz_), cid

def pull_all(db, course_, dry_run):
    r = helpers.get(QUIZZES_PATH.format(course_.canvas_id), dry_run=dry_run)
    quizzes = []
    print("pulling quiz questions")
    for quiz_json in tqdm(r):
        quiz_, _ = pull(db, course_, quiz_json, dry_run)
        if quiz_:
            quizzes.append(quiz_)
    return quizzes
