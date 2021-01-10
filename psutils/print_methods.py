
from __future__ import print_function
import sys

import psutils.log


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


trace = print
debug = print
info = print
verbose1 = print
verbose2 = print
verbose3 = print
warning = eprint
error = eprint
critical = eprint


if len(psutils.log.PSUTILS_LOGGER.handlers) > 0:

    trace = psutils.log.PSUTILS_LOGGER.trace
    debug = psutils.log.PSUTILS_LOGGER.debug
    verbose3 = psutils.log.PSUTILS_LOGGER.verbose3
    verbose2 = psutils.log.PSUTILS_LOGGER.verbose2
    verbose1 = psutils.log.PSUTILS_LOGGER.verbose1
    info = psutils.log.PSUTILS_LOGGER.info
    warning = psutils.log.PSUTILS_LOGGER.warning
    error = psutils.log.PSUTILS_LOGGER.error
    critical = psutils.log.PSUTILS_LOGGER.critical

    print = info
    eprint = error
