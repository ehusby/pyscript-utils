
from __future__ import print_function
import sys

import psutils.log


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


debug = print
info = print
warning = eprint
error = eprint
critical = eprint


if len(psutils.log.PSUTILS_LOGGER.handlers) > 0:

    debug = psutils.log.PSUTILS_LOGGER.debug
    info = psutils.log.PSUTILS_LOGGER.info
    warning = psutils.log.PSUTILS_LOGGER.warning
    error = psutils.log.PSUTILS_LOGGER.error
    critical = psutils.log.PSUTILS_LOGGER.critical

    print = info
    eprint = error
