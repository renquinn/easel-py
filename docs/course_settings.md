# Course Settings

[Canvas Reference](https://canvas.instructure.com/doc/api/courses.html#method.courses.update_settings)

These should be specified in `course.yaml` in the root of the course directory.
This file should not be tagged with a component type as the behavior is much
simpler. Simply list the fields you'd like to specify:

```
apply_assignment_group_weights: true
default_view: "syllabus"
```
