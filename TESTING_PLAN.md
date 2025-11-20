# Easel Testing Plan

This document outlines the strategy and scope for testing the Easel application. Our goal is to ensure code correctness, prevent regressions, and improve maintainability.

## 1. Tooling

-   **Test Runner:** `pytest`
-   **Mocking Library:** `pytest-mock` (a wrapper around `unittest.mock`)

To get started, install the necessary dependencies:
```bash
pip install pytest pytest-mock
```

## 2. Testing Strategy

We will focus primarily on **unit tests**, isolating and testing individual functions and methods. This requires extensive use of mocking to replace external dependencies like:
-   Network requests (`helpers.get`, `helpers.put`, etc.)
-   Database interactions (`tinydb`)
-   Filesystem operations (`open`, `os.path`, etc.)

Integration and end-to-end tests for the command-line interface are a lower priority and can be added later.

## 3. Test Coverage Breakdown

The following is a module-by-module breakdown of what needs to be tested.

### `easel/helpers.py`

-   [x] `isurl()`: Test with various valid and invalid URL formats.
-   [x] `make_nested_filename()`: Test correct string formatting.
--   [x] `filter_canvas_html()`: Test removal of Canvas comment block.
-   [x] `md2html()`: Test basic Markdown to HTML conversion.
-   [ ] `do_request()` (and by extension `get`, `put`, `post`, `delete`):
    -   Mock the `requests` library.
    -   Verify that the correct method, URL, headers, and payload are used.
    -   Test handling of successful responses (e.g., JSON decoding).
    -   Test handling of HTTP error codes.
    -   Test the `dry_run` flag to ensure no request is made.
-   [ ] `Config` class:
    -   Mock `pathlib.Path.home` and `open`.
    -   Test successful loading of a mock config file.
    -   Test handling of a missing or malformed config file.
-   [ ] `load_db()`: Mock `TinyDB` to ensure it's called with the correct path.

### `easel/course.py`

-   [x] `get_id_from_url()`: Test with various valid and invalid course URLs.
-   [ ] `Course` class:
    -   Test `__init__` for correct attribute assignment and syllabus filtering.
    -   Test `save()` by mocking the `db` object and `open` to verify correct data is saved.
    -   Test `remove()` by mocking the `db` object.
-   [ ] `find()`, `find_all()`, `match_course()`:
    -   Mock the `db` object with sample course data.
    -   Verify that the functions return the expected `Course` instances based on search criteria.
-   [ ] `pull()`: Mock `helpers.get` and verify a `Course` object is built correctly from the mock response.
-   [ ] `format_syllabus()`:
    -   This is a complex function requiring multiple mocks.
    -   Mock `open` to provide sample `syllabus.md` content with frontmatter.
    -   Mock `helpers.get_course_template_fields` and `helpers.get_global_template_fields`.
    -   Verify that template fields from all sources are correctly merged and rendered into the final HTML.
-   [ ] `push_syllabus()`, `update_grading_scheme()`, `update_settings()`:
    -   Mock `helpers.put`.
    -   Verify the correct payload is constructed and sent.
    -   Test the `dry_run` flag.

### `easel/component.py`

-   [x] `gen_filename()`: Test string formatting and slugification.
-   [x] `filter_fields()`: Test logic for keeping and removing dictionary keys.
-   [ ] `Component` class methods: These will primarily be tested through their subclass implementations (e.g., `Assignment`, `Page`), but we should have some baseline tests.
    -   `get_canvas_id()`: Mock `db` to test finding an existing ID.
    -   `save()`, `remove()`: Mock `db` to test database operations.
    -   `push()`: This is the most critical method.
        -   Test the "create" logic (when `get_canvas_id` returns `None`). Mock `helpers.post` and verify it's called correctly.
        -   Test the "update" logic (when `get_canvas_id` returns an ID). Mock `helpers.put` and verify it's called correctly.
        -   Verify that `preprocess` and `postprocess` are called.
    -   `pull()`: Mock `helpers.get`.

### `easel/canvas_id.py`

-   [ ] `CanvasID` class: Mock the `db` object to test `save()`, `remove()`, and `find_id()`.
-   [ ] `find_by_id()`, `find_by_prefix()`: Mock `db` with sample data and verify correct results are returned.

### Component Subclasses
*(e.g., `assignment.py`, `page.py`, `quiz.py`, `module.py`, etc.)*

For each component subclass:
-   [ ] Test the `build()` classmethod.
-   [ ] Test any component-specific `preprocess()` logic (e.g., `Assignment.get_assignment_group_id`). This will require mocking DB calls.
-   [ ] Test any component-specific `postprocess()` logic (e.g., `Quiz.postprocess` for handling questions).
-   [ ] Test any helper methods like `md()` to ensure correct content generation.
-   [ ] Test that `pull()` correctly constructs the object and its children (e.g., `Quiz.pull` pulling questions).

### `easel/commands.py` and `easel/__main__.py`

-   [ ] Testing the command-line interface is complex. This is a low priority. We can add end-to-end tests later that execute the script and check output or filesystem changes.
