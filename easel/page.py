from tqdm import tqdm

from easel import canvas_id
from easel import component
from easel import course
from easel import helpers
from easel import helpers_yaml

PAGES_PATH=course.COURSE_PATH+"/pages"
PAGE_PATH=PAGES_PATH+"/{}" # page url
TABLE="pages"
WRAPPER="wiki_page"
PAGES_DIR="pages"

class Page(component.Component):

    def __init__(self, url=None, title=None, body=None, published=None,
            front_page=None, todo_date=None, editing_roles=None,
            notify_of_update=None, filename="", student_todo_at=None,
            yaml_order=[]):
        super().__init__(create_path=PAGES_PATH, update_path=PAGE_PATH,
                db_table=TABLE, canvas_wrapper=WRAPPER, filename=filename,
                yaml_order=yaml_order)
        self.url = url
        self.title = title
        self.published = published
        self.front_page = front_page
        self.student_todo_at = todo_date
        if student_todo_at:
            self.student_todo_at = student_todo_at
        self.editing_roles = editing_roles
        self.notify_of_update = notify_of_update
        self.body = body

    def preprocess(self, db, course_, dry_run):
        if self.body:
            self.body = helpers.md2html(self.body.strip())

    def __repr__(self):
        return f"Page(title={self.title}, published={self.published})"

    @classmethod
    def build(cls, fields):
        defaults = {
                "front_page": False,
                "editing_roles": "teachers",
                }
        desired_fields = cls.__init__.__code__.co_varnames[1:]
        component.filter_fields(fields, desired_fields, defaults)
        if 'body' in fields:
            fields['body'] = helpers.filter_canvas_html(fields['body'])
        return Page(**fields)

# Needed for custom yaml tag
def constructor(loader, node):
    fields = helpers_yaml.construct_ordered_mapping(loader, node)
    return Page(**fields)

def pull_page(db, course_id, page_url, dry_run):
    page_ = helpers.get(PAGE_PATH.format(course_id, page_url), dry_run=dry_run)
    cid = canvas_id.find_by_id(db, course_id, page_.get('url'))
    if cid:
        page_['filename'] = cid.filename
    else:
        page_['filename'] = component.gen_filename(PAGES_DIR, page_.get('title', ''))
        cid = canvas_id.CanvasID(page_['filename'], course_id)
        cid.canvas_id = page_.get('url')
        cid.save(db)
    return Page.build(page_), cid

def pull_all(db, course_, dry_run):
    r = helpers.get(PAGES_PATH.format(course_.canvas_id),
            dry_run=dry_run)
    pages = []
    print("pulling page contents")
    for p in tqdm(r):
        page_, _ = pull_page(db, course_.canvas_id, p.get('url'), dry_run)
        pages.append(page_)
    return pages
