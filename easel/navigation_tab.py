import yaml

from easel import course
from easel import helpers
from easel import helpers_yaml

NAV_TABS_PATH=course.COURSE_PATH+"/tabs"
FILENAME="navigation.yaml"

class NavigationTab:

    def __init__(self, html_url=None, id=None, label=None, position=None,
            unused=None, url=None, full_url=None, visibility=None, type=None,
            hidden=None, filename=FILENAME):
        self.filename=filename
        self.html_url=html_url
        self.id=id
        self.label=label
        self.position=position
        self.visibility=visibility
        self.type=type
        self.hidden=hidden
        self.unused=unused
        self.url=url
        self.full_url=full_url

    def __repr__(self):
        return f"NavigationTab(label={self.label}, position={self.position}, hidden={self.hidden})"

class NavigationTabs:
    """The pull command (cmd_pull in commands.py) assumes that the pull
    function (component.py, overridden in NavigationTab above) returns the
    specific component that we're pulling. However, this is the first time we
    have a component type that is managed as a list and is not embedded inside
    of another component. The hack here is to create this wrapper class in
    which to embed our list of navigation tabs."""

    def __init__(self, tabs_list=[]):
        self.tabs = tabs_list
        self.filename = FILENAME

    def __repr__(self):
        tabs = ", ".join([tab.label for tab in self.tabs])
        return f"NavigationTabs({tabs})"

    def pull(self, db, course_, dry_run):
        path = NAV_TABS_PATH.format(course_.canvas_id)
        resp = helpers.get(path, dry_run=dry_run)
        nav_tabs = []
        for nav_tab in resp:
            nav_tabs.append(NavigationTab(**nav_tab))
        return NavigationTabs(nav_tabs)

    def sort(self):
        """Ensure tabs are in order of position"""
        self.tabs = sorted(self.tabs, key=lambda x: x.position)

    def yaml(self):
        self.sort()
        labels = []
        for tab in self.tabs:
            if not tab.hidden:
                labels.append(tab.label)
        return yaml.dump(labels)

# Needed for custom yaml tag
def constructor(loader, node):
    if not helpers_yaml.isSequenceNode(node):
        raise ValueError(f"Invalid yaml value {node} for NavigationTab")

    tabs = []
    position = 0
    for subnode in node.value:
        position += 1
        label = loader.construct_scalar(subnode)
        tab = NavigationTab(label=label, position=position, hidden=False)
        tabs.append(tab)
    return NavigationTabs(tabs)
