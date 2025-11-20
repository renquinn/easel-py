# Implement a Component Registry

Observation: The DIRS dictionary in `helpers.py` acts as a service locator,
mapping directory names to component modules. This is a form of tight coupling;
to add a new component, you must remember to modify this dictionary.

Recommendation: Implement a self-registering pattern for components. This will
decouple the command layer from the component implementations.

Instructions for the Editor Engineer:

1. In `easel/component.py`, create a dictionary at the module level called
   COMPONENT_REGISTRY.
2. Modify the Component class, possibly using a metaclass or
   `__init_subclass__`, so that every class that inherits from Component
   automatically registers itself in COMPONENT_REGISTRY. The key for
   registration should be the component's directory name (from the new local_dir
   class attribute proposed in point #1).
    - For example: `COMPONENT_REGISTRY['quizzes'] = <class 'easel.quiz.Quiz'>`.
3. Remove the DIRS dictionary from `helpers.py`.
4. Refactor any code that used the DIRS dictionary (likely in `commands.py` or
   `__main__.py`) to instead look up the appropriate component class from
   component.COMPONENT_REGISTRY. This makes component discovery automatic.
