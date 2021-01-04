# Easel

A Canvas course management tool.

## Operations

### Login

```
easel login <canvas_base_url> <api_token>
```

E.g.,

```
easel login https://school.instructure.com yourT0kenH3re
```

Only needs to be run once per client machine. Records the Canvas url and token
to be used for later.

### Init

```
easel init
```

Initializes the easel database in the current directory. Run this one time per
course directory.

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

```
easel push
```

Reads and pushes a single item of the given component type to the configured
courses. A push reads the information of each component stored locally and for
each one, makes a PUT request to Canvas. For now it only creates new components
on the Canvas course. The ability to update them will come in the future.

Works for the following components:

- assignments
- assignment groups
- courses
- external tools
- pages
- more to come!

```
easel push [component_filepath]
```

E.g.,

```
easel push pages/lesson-1.yaml
```

## File Structure

It is recommend to store component files in separate directories, named for
their component type (e.g., pages are stored in a directory called `pages`).
This is not required but may be in the future once pulling updates from Canvas
is enabled.

Each individual component is defined by a single file.

Components are defined using yaml. When a component has some associated
body/description content, it should be included in markdown as part of the
component's yaml configuration using a multiline string (see the `examples`
directory for examples).

## TODO

I'll try to keep this list in order, with the items I'm prioritizing to get done
sooner listed first.

- I've been assuming user pulls or pushes from the course's root directory. Need
  to search for the component dirs
- multiple courses (i.e., sections).
    - implicit iteration
        - push: pushes to all courses, unless specified (e.g., -c 02)
        - pull: pulls from all courses, checks for and reports any differences
            - need to add a prompt for overwrite, manually merge, or abort
            - need to track multiple canvas ids per component in the db. I'm
              saving the canvas id on each component as if it would be the same
              across all courses, but this is not the case.
- Figure out the workflow for editing page/assignment content. Canvas uses html,
  I'd prefer to express it in markdown.
  - First proposal: locally in markdown, convert to html when pushing. Don't
    edit content in Canvas (since we can't faithfully convert html to md).
    Pulling would not overwrite the component's contents.
- pull/push everything in transactions
    - use db as intermediate step, only go to Canvas if db transaction succeeded
    - workflow for pulling whether to overwrite, manually merge, or abort
    - When pushing, update database with result (e.g., when pushing to a new
      course, the canvas id will be different)
- represent dates as time.Time
    - API requires strings in ISO 8601 format: YYYY-MM-DDTHH:MM:SSZ (e.g., "2013-01-23T23:59:00-07:00")
- add a progress bar for pushing and pulling
- add a command to publish components rather than changing the published field
  in the file?

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
