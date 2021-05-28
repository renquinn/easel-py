from easel import component
from easel import course

EXT_TOOLS_PATH=course.COURSE_PATH+"/external_tools"
EXT_TOOL_PATH=EXT_TOOLS_PATH+"/{}"
EXT_TOOLS_TABLE="external_tools"

class ExternalTool(component.Component):

    def __init__(self, name="", consumer_key="", shared_secret="",
            config_type="", config_url="", filename=""):
        super().__init__(create_path=EXT_TOOLS_PATH, update_path=EXT_TOOL_PATH,
                db_table=EXT_TOOLS_TABLE, filename=filename)
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
