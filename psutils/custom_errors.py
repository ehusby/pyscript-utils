
class VersionError(Exception):
    def __init__(self, msg=""):
        super(Exception, self).__init__(msg)

class DeveloperError(Exception):
    def __init__(self, msg=""):
        super(Exception, self).__init__(msg)

class ScriptArgumentError(Exception):
    def __init__(self, msg=""):
        super(Exception, self).__init__(msg)

class InvalidArgumentError(Exception):
    def __init__(self, msg=""):
        super(Exception, self).__init__(msg)

class ExternalError(Exception):
    def __init__(self, msg=""):
        super(Exception, self).__init__(msg)

class DimensionError(Exception):
    def __init__(self, msg=""):
        super(Exception, self).__init__(msg)
