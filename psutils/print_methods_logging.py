
from __future__ import print_function
import sys

import psutils.log


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


psutils.log.setup_logging()

trace = psutils.log.PSUTILS_LOGGER.trace
debug = psutils.log.PSUTILS_LOGGER.debug
verbose3 = psutils.log.PSUTILS_LOGGER.verbose3
verbose2 = psutils.log.PSUTILS_LOGGER.verbose2
verbose1 = psutils.log.PSUTILS_LOGGER.verbose1
info = psutils.log.PSUTILS_LOGGER.info
warning = psutils.log.PSUTILS_LOGGER.warning
error = psutils.log.PSUTILS_LOGGER.error
critical = psutils.log.PSUTILS_LOGGER.critical
