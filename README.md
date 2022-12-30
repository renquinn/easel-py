# Easel

A Canvas course management tool.

## Installation

```
pip install easel-cli
```

To install from the root of the repository:

```
pip install -e .
```

## Usage

When connected to a Canvas course, easel will read in a yaml file and create the
corresponding component in Canvas on that course. Currently, easel requires you
to run its commands from the root of your course directory (where the component
subdirectories are located). This is where easel will initialize its database:
`.easeldb`.

### Getting Started

For each of these operations, refer to their detailed description and usage
below.

1. Tell easel about your Canvas instance (only needs to be run once):
    `easel login <canvas_base_url> <api_token>`
2. Initialize easel in a course-specific directory: `easel init`
3. Add a course or courses (i.e., sections):
    `easel course add <canvas_course_url>`
4. Create yaml files describing your course content and push them to your
   course: `easel push [component_filepath ...]`

Easel makes it easy to not have to start from scratch by first pulling the
material from a previous course and pushing it to a new course:

1. Tell easel about your Canvas instance:
    `easel login <canvas_base_url> <api_token>`
2. Initialize easel in a course-specific directory: `easel init`
3. Add the previous course: `easel course add <previous_canvas_course_url>`
4. Pull everything from it: `easel pull`
5. Add the new course: `easel course add <new_canvas_course_url>`
6. Push everything to the new course: `easel --course <new_course_id> push`
7. At this point, you may remove your old course: `easel course remove <old_course_id>`

## Individual Component References

These are the components currently managed by easel. For configuration, see the
linked documentation.

- [Assignments](docs/component_fields/assignment.md)
- [Assignment Groups](docs/component_fields/assignment_group.md)
- [External Tools](docs/component_fields/external_tool.md)
- [Course Grading Scheme](docs/course_grading_scheme.md)
- [Course Settings](docs/course_settings.md)
- [Modules](docs/component_fields/module.md)
- [Navigation Tabs](docs/component_fields/navigation.md)
- [Pages](docs/component_fields/page.md)
- [Quizzes](docs/component_fields/quiz.md)
- [Syllabus](docs/syllabus.md)

## Command Reference

### Login

```
easel login <canvas_base_url> <api_token>
```

E.g.,

```
easel login https://school.instructure.com yourT0kenH3re
```

Only needs to be run once per client machine. Records the Canvas url and token
to be used later. Canvas tokens can be generated in
"Account->Settings->+New Access Token".

### Init

```
easel init
```

Run this one time per course directory. It will initialize the easel database in
the current directory. It will also create subdirectories for each Canvas
component type that easel supports.

At this time, easel requires components to be organized by directory but this is
hopefully a temporary restriction.

### Course

```
easel course add <canvas_course_url>
```

E.g.,

```
easel course add https://school.instructure.com/courses/615446
```

Hooks up the database to a Canvas course. Run this one time per Canvas course
(once per section taught per semester).

```
easel course list
```

List all Canvas courses that are tracked in the database.

### Push

Reads in and pushes a specific component (or multiple components) to the
configured courses. A push reads the information of each component stored
locally and for each one, makes a POST or PUT request to Canvas, depending on
whether you are creating or updating the component in the Canvas course.

```
easel push
```

or to push to a specific course:

```
easel --course <course_id> push
```

To push a specific component or components:

```
easel push [component_filepath ...]
```

E.g.,

```
easel push pages/lesson-1.yaml
```

Notes on pushing files:

- Files placed in the `files` directory will be pushed as they are (ignoring
  the `files` parent directory).
- Supports multiple filename arguments and wildcards for batch pushing.
- Use the `--hidden` flag to unpublish the file(s) as hidden when pushed (by
  default canvas publishes files when you upload them).
- When pushing a directory, `easel` will push all of its child files.

Course filtering:

Use the `--course` flag (alternatively `-c`) to specify a subset of your
courses. I prefer to use the section number to identify a course. For example,
to push a page to only sections 01 and 02, I would use this command:

```
easel push -c 01 -c 02 pages/lesson-1.yaml
```

### Remove

Remove a given component(s) from the canvas course. This does not delete the
yaml file or the local database entry for the component. But it will remove the
database record which tracks that component in Canvas (i.e., it's Canvas ID).

```
easel remove [component_filepath ...]
```

E.g.,

```
easel remove pages/lesson-1.yaml
```

Note for files:

- Supports multiple filename arguments and wildcards for batch removing.
- When removing a directory, `easel` will remove all of its child files (however
  the empty directory will remain in Canvas).

## File Structure

For now it is required to store component files in separate directories, named
for their component type (e.g., store definition files for pages in a directory
called `pages`). This requirement may be removed in the future.

Each individual component is defined by a single file using yaml. When a
component has some associated body/description content, it should be included in
markdown as part of the component's yaml configuration using a multiline string
(see the `examples` directory for examples).

## Dates

When specifying dates (e.g., due_at, unlock_at, lock_at),
[ISO 8601 format](https://en.wikipedia.org/wiki/ISO_8601) should be used. This
is temporary until I can build out an internal date management system.

## TODO

I'll try to keep this list in order, with the items I'm prioritizing to get done
sooner listed first.

- add a new command which generates a component config file formatted and filled
  with common options
    - -i flag could prompt user to enter required options interactively
- manage datetimes for user
    - relative semester/time specification
        - e.g.,
            - module 1 day 2 start of class,
            - module 6 class 1 start of class,
            - week 4 day -1 end of class
            - start of week 2 (first day of the week in the morning)
            - end of week 3 (last day of the week at midnight)
        - instead of weeks use modules?
            - define module with respect to 150-minute chunks (equivalent of one
              week)
            - gives us more flexibility for holidays
            - user specifies dependency tree for modules in terms of
              prerequisite modules
            - easel schedules the modules based on semester dates
            - deadlines are declared with respect to the module (which may carry
              over to another week, depending on holidays, etc.
        - fields
            - due_at
                - detect if already in iso format and if not, parse as the
                  relative formate
            - length (for modules only)
                - the number of 50 minute blocks in this module
            - previous module?
            - next module?
        - implementation
            - detect semester dates
                - start and end dates (including finals?)
                - holidays
            - map modules to the semester based on module length and semester dates
                - if no modules, just use weeks
    - API requires strings in ISO 8601 format: YYYY-MM-DDTHH:MM:SSZ (e.g., "2013-01-23T23:59:00-07:00")
    - automate daylight savings translations
    - maybe consider automating final exam times too
- test other types of module items
    - working:
        - Page
        - Assignment
        - File
        - SubHeader
        - ExternalUrl
    - need testing:
        - Discussion
        - Quiz
          - pulls down as an assignment?
        - ExternalTool
- better logging
- I've been assuming user pulls or pushes from the course's root directory. Need
  to search for the component dirs
- Figure out the workflow for editing page/assignment content. Canvas uses html,
  I'd prefer to express it in markdown.
  - First proposal: locally in markdown, convert to html when pushing. Don't
    edit content in Canvas (since we can't faithfully convert html to md).
    Pulling would not overwrite the component's contents.
- multiple courses (i.e., sections).
    - implicit iteration
        - push: pushes to all courses, unless specified (e.g., -c 02)
        - pull: pulls from all courses, checks for and reports any differences
            - need to add a prompt for overwrite, manually merge, or abort
- pull/push everything in transactions
    - use db as intermediate step, only go to Canvas if db transaction succeeded
    - workflow for pulling whether to overwrite, manually merge, or abort
    - When pushing, update database with result (e.g., when pushing to a new
      course, the canvas id will be different)
- merge prompt
    - https://twitter.com/_wilfredh/status/1413002445366591496
- add a progress bar for pushing and pulling
- add a command to publish components rather than changing the published field
  in the file?
- GUI?
    - https://github.com/willmcgugan/rich
    - https://github.com/willmcgugan/textual
    - https://github.com/pfalcon/picotui
    - https://docs.python.org/3/howto/curses.html
- support Formula type quiz questions. it's almost there but it probably
  requires the weird json list formatting as with QuizQuestion.answers. See the
  TODO comment in `__iter__` from `quiz_question.py`
- delete folders
    - since I don't explicitly create folders, I don't have their ids, so I'd
      have to get that at some point and track it to eventually delete it
    - https://canvas.instructure.com/doc/api/files.html#method.folders.api_destroy
- auto generate syllabus parts

### Thoughts

- Enforce directories? (e.g., pages, assignments, modules)
    - Or when pushing a component, save its filepath in the db
- Component files that only have yaml (no md or html), should the extension be
  yaml or stay consistent with md?
- We should enable expressing dates/times that are relative to the section
  meeting time (e.g., beginning of class, end of class, Fridays)
- would it be worth adding in grading stuff eventually?
- Some fields would be useful to Easel but not necessary for instructor edits
  (e.g., record ids, component status).
  Do we keep those in the DB but not write them to file?
- should quiz questions be in their own file? Options:
    - a single quiz's questions in one file. easier to implement but it would be
      harder to reuse them
    - one file per question, easy to move around, but how to uniquely identify
      each question? (for the name of the file)
    - one file per question category (e.g., all requrements engineering
      questions) this is probably the best user-focused approach, but harder to
      implement?
- Question groups only work with question banks. We can't create question banks
  via the api. What other option do we have? Ideally we create a question group
  directly with the questions that should go in it. E.g.,
  ```
  - question_name: g1
    question_type: group
    questions:
      - quiz_questions/functions.yaml
      - quiz_questions/functions.yaml
      - quiz_questions/functions.yaml
  ```
  The preprocessor would intercept the `question_type` (it's invalid anyway) and
  make the api call to create the group, passing in the questions. So remember
  that in case they open up question groups to work by specifying a question
  directly.
- by default, canvas courses do not enable weighted assignment groups
    - allow users to update the course with this (or make it the default?)
    - I set it up for now to automatically weight (default to True in
      push_syllabus of course.py)
