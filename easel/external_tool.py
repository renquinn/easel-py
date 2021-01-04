from easel import component
from easel import course

EXT_TOOLS_PATH=course.COURSE_PATH+"/external_tools"

class ExternalTool(component.Component):

    def __init__(self, name, consumer_key, shared_secret, config_type, config_url):
        component.Component.__init__(self, EXT_TOOLS_PATH)
        self.name = name
        self.consumer_key = consumer_key
        self.shared_secret = shared_secret
        self.config_type = config_type
        self.config_url = config_url

    def __repr__(self):
        return f"ExternalTool(name={self.name})"

# Needed for custom yaml tag
def constructor(loader, node):
    return ExternalTool(**loader.construct_mapping(node))
