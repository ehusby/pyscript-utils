
import psutils.custom_errors as cerr
from psutils.versionstring import VersionString
from psutils.globals import PYTHON_VERSION

import os


MODULE_VERSION_NUM = "1.0"
PYTHON_VERSION_REQUIRED_MIN = "2.7"

if PYTHON_VERSION < VersionString(PYTHON_VERSION_REQUIRED_MIN):
    raise cerr.VersionError("Python version ({}) is below required minimum ({})".format(
        PYTHON_VERSION, PYTHON_VERSION_REQUIRED_MIN))

MODULE_DIR = os.path.dirname(os.path.abspath(os.path.realpath(__file__)))
