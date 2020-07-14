
import logging
import sys


class LoggerDebugFilter(logging.Filter):
    def filter(self, rec):
        return rec.levelno == logging.DEBUG

class LoggerInfoFilter(logging.Filter):
    def filter(self, rec):
        return rec.levelno == logging.INFO


psutils_LOGGER = logging.getLogger(__name__)
LOGFMT_BASIC = logging.Formatter("%(asctime)s :: %(levelname)s -- %(message)s")
LOGFMT_DEEP = logging.Formatter("%(asctime)s (PID %(process)d) :: %(pathname)s:%(lineno)s :: %(levelname)s -- %(message)s")


def setup_logging(logger=None, level=logging.INFO, log_format=None,
                  outfile=None, errfile=None, dup_err_in_outfile=False,
                  capture_warnings=None):
    if logger is None:
        logger = psutils_LOGGER
    if level is not None:
        logger.setLevel(level)

    error_fh_files = []
    if errfile is not None:
        error_fh_files.append(errfile)
    if outfile is not None and (errfile is None or dup_err_in_outfile):
        error_fh_files.append(outfile)
    if len(error_fh_files) == 0:
        error_fh_files.append(None)

    if capture_warnings is True:
        # Have logger handle Python warnings
        warn_logger = logging.getLogger('py.warnings')
        warn_logger.setLevel(level)
        if len(warn_logger.handlers) == 0:
            for file in error_fh_files:
                warn_handler = logging.StreamHandler(sys.stderr) if file is None else logging.FileHandler(file)
                warn_handler.setLevel(logging.WARNING)
                warn_handler.setFormatter(LOGFMT_BASIC if log_format is None else log_format)
                warn_logger.addHandler(warn_handler)
        logging.captureWarnings(True)
    elif capture_warnings is False:
        # warn_logger = logging.getLogger('py.warnings')
        # warn_logger.handlers = []
        logging.captureWarnings(False)

    if outfile is None and len(logger.handlers) > 0:
        return

    debug_handler = logging.StreamHandler(sys.stdout) if outfile is None else logging.FileHandler(outfile)
    debug_handler.setLevel(logging.DEBUG)
    debug_handler.setFormatter(LOGFMT_DEEP if log_format is None else log_format)
    debug_handler.addFilter(LoggerDebugFilter())
    logger.addHandler(debug_handler)

    info_handler = logging.StreamHandler(sys.stdout) if outfile is None else logging.FileHandler(outfile)
    info_handler.setLevel(logging.INFO)
    info_handler.setFormatter(LOGFMT_BASIC if log_format is None else log_format)
    info_handler.addFilter(LoggerInfoFilter())
    logger.addHandler(info_handler)

    for file in error_fh_files:
        error_handler = logging.StreamHandler(sys.stderr) if file is None else logging.FileHandler(file)
        error_handler.setLevel(logging.WARNING)
        error_handler.setFormatter(LOGFMT_DEEP if log_format is None else log_format)
        logger.addHandler(error_handler)
