# Navigation Tabs

[Canvas Reference](https://canvas.instructure.com/doc/api/tabs.html)

To simplify things, easel only accepts a list of strings as configuration for
the course navigation. This list should be in the root of the easel-managed
directory and named `navigation.yaml`.

Here is an example:

```
!NavigationTabs
- Announcements
- Assignments
- Grades
- People
- Discussions
- Syllabus
- Quizzes
- Files
- My Media
- Media Gallery
- CoursEval
```

Note that Canvas does not allow users to manage the Home or Settings tab so
easel will ignore them if included in the yaml.
