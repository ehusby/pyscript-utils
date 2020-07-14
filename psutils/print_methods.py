
from __future__ import print_function
import sys

import psutils.logger


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


debug = print
info = print
warning = eprint
error = eprint
critical = eprint


if len(psutils.logger.psutils_LOGGER.handlers) > 0:

    debug = psutils.logger.psutils_LOGGER.debug
    info = psutils.logger.psutils_LOGGER.info
    warning = psutils.logger.psutils_LOGGER.warning
    error = psutils.logger.psutils_LOGGER.error
    critical = psutils.logger.psutils_LOGGER.critical

    print = info
    eprint = error
