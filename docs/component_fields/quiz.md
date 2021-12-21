### Quizzes

The following fields are recognized by easel for quizzes.

See the
[Canvas documentation](https://canvas.instructure.com/doc/api/quizzes.html)
for quizzes.

- title
- published
- description
- assignment_group (the name of the assignment group)
- points_possible
- allowed_attempts
- due_at
- unlock_at
- lock_at
- quiz_type
- time_limit
- shuffle_answers
- hide_results
- show_correct_answers
- show_correct_answers_last_attempt
- show_correct_answers_at
- hide_correct_answers_at
- scoring_policy
- one_question_at_a_time
- cant_go_back
- access_code
- ip_filter
- one_time_results
- only_visible_to_overrides
- anonymous_submissions
- description
- quiz_questions (a list of quiz_question objects, see below)

Each quiz question can have the following fields:

[(Canvas documentation)](https://canvas.instructure.com/doc/api/quiz_questions.html)

- question_name
- question_type
- question_text
- points_possible
- position
- correct_comments
- incorrect_comments
- neutral_comments
- matching_answer_incorrect_matches
- text_after_answers
- answers (a list of answer objects, see below)

Each quiz question answer can have the following fields:

- answer_text
- answer_weight
- blank_id (for fill in multiple blanks or multiple dropdowns question questions)
- answer_match_left (for matching questions)
- answer_match_right (for matching questions)
- numerical_answer_type (for numerical questions), possible values:
    - exact_answer
    - range_answer
    - precision_answer
- answer_exact (for numerical questions)
- answer_error_margin (for numerical questions)
- answer_range_start (for numerical questions)
- answer_range_end (for numerical questions)
- answer_approximate (for numerical questions)
- answer_precision (for numerical questions)
