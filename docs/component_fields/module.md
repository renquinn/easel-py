
### Modules

The following fields are recognized by easel for modules.

See the
[Canvas documentation](https://canvas.instructure.com/doc/api/modules.html)
for modules.

- name
- published
- position
- unlock_at
- require_sequential_progress
- prerequisite_module_ids
- items (a list of module item objects, see below)

Each module item can have the following fields:

- item
    - this is a local filename that represents the yaml file for the item you
      want to add to the module
    - if you don't specify any other option for this item, you can just use the
      name of the file as a string without creating a yaml object for it
    - only Pages and Assignments work for now (see TODO section below)
- indent
- new_tab

