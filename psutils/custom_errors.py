
class VersionError(Exception):
    def __init__(self, msg=""):
        super(VersionError, self).__init__(msg)

class DeveloperError(Exception):
    def __init__(self, msg=""):
        super(DeveloperError, self).__init__(msg)

class ScriptArgumentError(Exception):
    def __init__(self, msg=""):
        super(ScriptArgumentError, self).__init__(msg)

class InvalidArgumentError(Exception):
    def __init__(self, msg=""):
        super(InvalidArgumentError, self).__init__(msg)

class ExternalError(Exception):
    def __init__(self, msg=""):
        super(ExternalError, self).__init__(msg)

class DimensionError(Exception):
    def __init__(self, msg=""):
        super(DimensionError, self).__init__(msg)
