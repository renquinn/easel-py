# Encapsulate Course and Database Context

Observation: Nearly every function and method takes db and course_ as arguments.
This "tramp data" is passed through multiple layers, creating long and
repetitive function signatures.

Recommendation: Create a Context object that encapsulates the database
connection, the current course object, and potentially the API client. This
object can be created once per command execution and passed around.

Instructions for the Editor Engineer:

1. Create a new class, perhaps EaselContext, in a new `easel/context.py` file.

```python
# easel/context.py
class EaselContext:
   def __init__(self, db_connection, course_object):
       self.db = db_connection
       self.course = course_object
       # You could also initialize your API client here
```

2. In `commands.py`, at the beginning of each command function (like cmd_pull,
   cmd_push), instantiate this EaselContext object.
3. Refactor function signatures across the application to accept a single
   context object instead of db, course_.
    - For example, `quiz.pull(db, course_, quiz_, dry_run)` becomes
      `quiz.pull(context, quiz_, dry_run)`. Inside the function, you would
      access context.db and context.course.
4. This change will be widespread but will significantly clean up the method
   signatures and make it easier to add shared resources (like a logger) in the
   future.
