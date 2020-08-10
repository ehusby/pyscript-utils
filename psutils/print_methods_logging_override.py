
from __future__ import print_function

import psutils.logger


psutils.logger.setup_logging()
debug = psutils.logger.PSUTILS_LOGGER.debug
info = psutils.logger.PSUTILS_LOGGER.info
warning = psutils.logger.PSUTILS_LOGGER.warning
error = psutils.logger.PSUTILS_LOGGER.error
critical = psutils.logger.PSUTILS_LOGGER.critical

print = info
eprint = error
