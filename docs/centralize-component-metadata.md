# Centralize Component Metadata

Observation: Each component module (e.g., `easel/assignment.py`,
`easel/quiz.py`) defines module-level constants for API paths, database tables,
directory names, and API wrappers (e.g., QUIZZES_PATH, QUIZZES_TABLE,
QUIZZES_DIR, WRAPPER). This is repeated for every component type.

Recommendation: Move this metadata into the component classes themselves as
class attributes. The base Component class can then use these attributes to
perform generic operations, eliminating redundant logic in the subclasses.

Example Change (in `easel/quiz.py`):

Remove the module-level constants:

```python
# REMOVE THESE
QUIZZES_PATH=course.COURSE_PATH+"/quizzes"
QUIZ_PATH=QUIZZES_PATH+"/{}"
QUIZZES_TABLE="quizzes"
WRAPPER="quiz"
QUIZZES_DIR="quizzes"
```

Add them as class attributes to the Quiz class:

```python
class Quiz(component.Component):
   # ADD THESE
   api_path_stub = "quizzes"
   db_table = "quizzes"
   api_wrapper = "quiz"
   local_dir = "quizzes"

   def __init__(self, title=None, published=None, ...):
       # ... existing init ...
```

Instructions for the Editor Engineer:

1. Go through each component module (`assignment.py`, `assignment_group.py`,
   `module.py`, `page.py`, `quiz.py`).
2. For each module, identify the module-level constants defining paths, tables,
   wrappers, and directories.
3. Move these constants inside their corresponding Component subclass as class
   attributes with standardized names (e.g., `api_path_stub`, `db_table`,
   `api_wrapper`, `local_dir`).
4. Refactor the base Component class methods (push, pull, find, etc.) to
   construct API paths and database queries dynamically using these new class
   attributes (self.api_path_stub, self.db_table, etc.) instead of relying on
   passed-in values.
