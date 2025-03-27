import expath.handlers.meta as metahandlers


class ConfigsPathHandler(metahandlers.EntryPointsPathHandler):
    def __init__(self):
        super().__init__("configs")
