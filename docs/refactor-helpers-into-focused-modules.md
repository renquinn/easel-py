# Refactor `helpers.py` into Focused Modules

Observation: The `helpers.py` module is a "god object" module. It handles API
requests, configuration management, utility functions (`md2html`), and contains
a critical DIRS dictionary that maps strings to modules. This violates the
Single Responsibility Principle.

Recommendation: Break `helpers.py` into smaller, more focused modules.

Instructions for the Editor Engineer:

1. Create a new file: `easel/api.py` or `easel/canvas_api.py`.
    - Move all network request functions (`delete`, `get`, `post`, `put`,
      `do_request`, `download_file`) from `helpers.py` into this new file.
    - Move API constants like API and HTTPS into this file as well.
2. Create a new file: `easel/config.py`.
    - Move the Config class and related functions (`write_config`, `load_db`)
      from `helpers.py` into this file.
3. Create a new file: `easel/utils.py`.
    - Move general utility functions (`isurl`, `make_nested_filename`,
      `filter_canvas_html`, `md2html`) into this file.
4. Update all imports across the project to reflect these changes. The
   `helpers.py` file should ideally be much smaller or completely removed.
