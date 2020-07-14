
import platform

import psutils.custom_errors as cerr

from psutils.versionstring import VersionString


PYTHON_VERSION = VersionString(platform.python_version())
PYTHON_VERSION_LT_3 = (PYTHON_VERSION < VersionString(3))

SYSTYPE = platform.system()
SYSTYPE_WINDOWS = 'Windows'
SYSTYPE_LINUX = 'Linux'
SYSTYPE_DARWIN = 'Darwin'
SYSTYPE_CHOICES = [
    SYSTYPE_WINDOWS,
    SYSTYPE_LINUX,
    SYSTYPE_DARWIN
]
if SYSTYPE not in SYSTYPE_CHOICES:
    raise cerr.DeveloperError("platform.system() value '{}' is not supported".format(SYSTYPE))

PATH_SEPARATORS_LIST = ['/', '\\']
