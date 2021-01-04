from easel import component
from easel import course
from easel import helpers

PAGES_PATH=course.COURSE_PATH+"/pages"

class Page(component.Component):

    def __init__(self, url=None, title=None, body=None, published=None,
            front_page=None, todo_date=None, editing_roles=None,
            notify_of_update=None):
        component.Component.__init__(self, PAGES_PATH)
        self.url = url
        self.title = title
        self.published = published
        self.front_page = front_page
        self.todo_date = todo_date
        self.editing_roles = editing_roles
        self.notify_of_update = notify_of_update
        if body:
            self.body = helpers.md2html(body.strip())
        else:
            self.body = body

    def __iter__(self):
        fields = dict(super().__iter__())
        wrapped = {"wiki_page": fields}
        yield from wrapped.items()

    def __repr__(self):
        return f"Page(title={self.title}, published={self.published})"


# Needed for custom yaml tag
def constructor(loader, node):
    return Page(**loader.construct_mapping(node))
