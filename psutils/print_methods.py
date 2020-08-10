
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


if len(psutils.logger.PSUTILS_LOGGER.handlers) > 0:

    debug = psutils.logger.PSUTILS_LOGGER.debug
    info = psutils.logger.PSUTILS_LOGGER.info
    warning = psutils.logger.PSUTILS_LOGGER.warning
    error = psutils.logger.PSUTILS_LOGGER.error
    critical = psutils.logger.PSUTILS_LOGGER.critical

    print = info
    eprint = error
