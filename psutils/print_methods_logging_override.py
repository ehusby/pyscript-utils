
from __future__ import print_function

import psutils.logger


psutils.logger.setup_logging()
debug = psutils.logger.psutils_LOGGER.debug
info = psutils.logger.psutils_LOGGER.info
warning = psutils.logger.psutils_LOGGER.warning
error = psutils.logger.psutils_LOGGER.error
critical = psutils.logger.psutils_LOGGER.critical

print = info
eprint = error
