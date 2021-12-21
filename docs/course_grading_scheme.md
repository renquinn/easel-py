# Grading Scheme

[Canvas Reference](https://canvas.instructure.com/doc/api/grading_standards.html)

- title
- grading_scheme_entry

The grading_scheme_entry field is a list of GradingSchemeEntry objects, each
with the fields:

- name
- value

Here is an example grading scheme:

```
!GradingScheme
title: My Favorite Grading Scheme
grading_scheme_entry:
  - name: A
    value: 94
  - name: A-
    value: 90
  - name: B+
    value: 87
  - name: B
    value: 84
  - name: B-
    value: 80
  - name: C+
    value: 77
  - name: C
    value: 74
  - name: C-
    value: 70
  - name: D+
    value: 67
  - name: D
    value: 64
  - name: D-
    value: 60
  - name: F
    value: 0
```
