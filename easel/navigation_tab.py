import logging
import yaml

from easel import component
from easel import course
from easel import helpers
from easel import helpers_yaml

NAV_TABS_PATH=course.COURSE_PATH+"/tabs"
NAV_TAB_PATH=NAV_TABS_PATH+"/{}"
FILENAME="navigation.yaml"

class NavigationTab(component.Component):

    def __init__(self, html_url=None, id=None, label=None, position=None,
            unused=None, url=None, full_url=None, visibility=None, type=None,
            hidden=None, filename=FILENAME):
        super().__init__(filename=filename)
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

    def gen_fields(self):
        keep = ["hidden", "position"]
        fields = vars(self)
        for field in fields.items():
            if field[0] in keep and field[1] is not None:
                yield field

    def push(self, db, course_, dry_run):
        path = NAV_TAB_PATH.format(course_.canvas_id, self.id)
        resp = helpers.put(path, self, dry_run=dry_run)
        if isinstance(resp, dict):
            for key in ["message", "errors"]:
                if key in resp:
                    logging.error(resp[key])

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
    position = 2 # 1-based and position 1 is not valid (for Home)
    for subnode in node.value:
        label = loader.construct_scalar(subnode)
        if label in ["Home", "Settings"]:
            logging.warn(f"Canvas does not allow managing the {label} tab. " \
                    "If you don't remove this label from your yaml, the " \
                    "other tabs may not be positioned correctly.")
        tab = NavigationTab(label=label, position=position, hidden=False)
        tabs.append(tab)
        position += 1
    return NavigationTabs(tabs)

def push(db, course_, dry_run):
    remote = NavigationTabs().pull(db, course_, dry_run)
    local = helpers_yaml.read(FILENAME)
    hidden = []
    for remote_tab in remote.tabs:
        # Per Canvas docs: "Home and Settings tabs are not manageable, and
        # can't be hidden or moved"
        if remote_tab.id in ['home', 'settings']:
            continue
        found = False
        for local_tab in local.tabs:
            # we want to update a tab if 1. we have it locally in a different
            # position than what's currently in canvas, OR 2. the remote tab is
            # hidden but it's specified locally (i.e., we want it not hidden)
            if (remote_tab.label == local_tab.label
                    and (remote_tab.position != local_tab.position
                    or remote_tab.hidden != local_tab.hidden)):
                # local tabs are from the yaml and only have label, position,
                # and hidden fields, but we need the id
                local_tab.id = remote_tab.id
                local_tab.push(db, course_, dry_run)
                found = True
                break
        if not found:
            hidden.append(remote_tab)

    print("The following navigation tabs are or will be made hidden:")
    for tab in hidden:
        print("\t-", tab.label)
        # we also want to push a tab if it's not hidden in Canvas but it wasn't
        # included in the local yaml
        if not tab.hidden:
            tab.hidden = True
            tab.push(db, course_, dry_run)
