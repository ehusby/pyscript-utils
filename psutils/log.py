
import functools
import logging
import os
import sys

import psutils.argtype as psu_at


def addLoggingLevel(levelName, levelNum, methodName=None):
    """
    Comprehensively adds a new logging level to the `logging` module and the
    currently configured logging class.

    `levelName` becomes an attribute of the `logging` module with the value
    `levelNum`. `methodName` becomes a convenience method for both `logging`
    itself and the class returned by `logging.getLoggerClass()` (usually just
    `logging.Logger`). If `methodName` is not specified, `levelName.lower()` is
    used.

    To avoid accidental clobberings of existing attributes, this method will
    raise an `AttributeError` if the level name is already an attribute of the
    `logging` module or if the method name is already present

    Example
    -------
    >>> addLoggingLevel('TRACE', logging.DEBUG - 5)
    >>> logging.getLogger(__name__).setLevel("TRACE")
    >>> logging.getLogger(__name__).trace('that worked')
    >>> logging.trace('so did this')
    >>> logging.TRACE
    5

    """
    if not methodName:
        methodName = levelName.lower()

    if hasattr(logging, levelName):
       raise AttributeError('{} already defined in logging module'.format(levelName))
    if hasattr(logging, methodName):
       raise AttributeError('{} already defined in logging module'.format(methodName))
    if hasattr(logging.getLoggerClass(), methodName):
       raise AttributeError('{} already defined in logger class'.format(methodName))

    # This method was inspired by the answers to Stack Overflow post
    # http://stackoverflow.com/q/2183233/2988730, especially
    # http://stackoverflow.com/a/13638084/2988730
    def logForLevel(self, message, *args, **kwargs):
        if self.isEnabledFor(levelNum):
            self._log(levelNum, message, args, **kwargs)
    def logToRoot(message, *args, **kwargs):
        logging.log(levelNum, message, *args, **kwargs)

    logging.addLevelName(levelNum, levelName)
    setattr(logging, levelName, levelNum)
    setattr(logging.getLoggerClass(), methodName, logForLevel)
    setattr(logging, methodName, logToRoot)

try:
    addLoggingLevel('TRACE', logging.DEBUG - 1)
    addLoggingLevel('VERBOSE1', logging.INFO - 1)
    addLoggingLevel('VERBOSE2', logging.INFO - 2)
    addLoggingLevel('VERBOSE3', logging.INFO - 3)
except AttributeError:
    pass

LEVEL_TRACE = logging.TRACE
LEVEL_DEBUG = logging.DEBUG
LEVEL_VERBOSE3 = logging.VERBOSE3
LEVEL_VERBOSE2 = logging.VERBOSE2
LEVEL_VERBOSE1 = logging.VERBOSE1
LEVEL_INFO = logging.INFO
LEVEL_WARNING = logging.WARNING
LEVEL_ERROR = logging.ERROR
LEVEL_CRITICAL = logging.CRITICAL


##############################

### Argument globals ###

## Argument strings ("ARGSTR_")
ARGSTR_LOG_OUTFILE = '--log-outfile'
ARGSTR_LOG_ERRFILE = '--log-errfile'
ARGSTR_LOG_TASK_OUTEXT = '--log-task-outext'
ARGSTR_LOG_TASK_ERREXT = '--log-task-errext'
ARGSTR_LOG_TASK_OUTDIR = '--log-task-outdir'
ARGSTR_LOG_LEVEL = '--log-level'
ARGSTR_LOG_TASK_LEVEL = '--log-task-level'
ARGSTR_LOG_MODE = '--log-mode'
ARGSTR_LOG_APPEND = '--log-append'
ARGSTR_LOG_OVERWRITE = '--log-overwrite'

## Argument groups ("ARGGRP_" lists of "ARGSTR_" argument strings)
ARGGRP_LOGGING = [
    ARGSTR_LOG_OUTFILE,
    ARGSTR_LOG_ERRFILE,
    ARGSTR_LOG_TASK_OUTEXT,
    ARGSTR_LOG_TASK_ERREXT,
    ARGSTR_LOG_TASK_OUTDIR,
]
ARGGRP_OUTDIR = [
    ARGSTR_LOG_TASK_OUTDIR,
]

## Argument collections ("ARGCOL_" lists of "ARGGRP_" argument strings)
ARGCOL_MUT_EXCL_SET = [
    [ARGSTR_LOG_APPEND, ARGSTR_LOG_OVERWRITE],
]
# ARGCOL_MUT_EXCL_PROVIDED = [
#     [ARGSTR_LOG_APPEND, ARGSTR_LOG_OVERWRITE, ARGSTR_LOG_MODE],
# ]
ARGCOL_MUT_EXCL_PROVIDED = []

## Argument choices (declare "ARGCHO_{ARGSTR}_{option}" options followed by list of all options as "ARGCHO_{ARGSTR}")
ARGCHO_LOG_LEVEL_TRACE = 'TRACE'
ARGCHO_LOG_LEVEL_DEBUG = 'DEBUG'
ARGCHO_LOG_LEVEL_VERBOSE3 = 'VERBOSE3'
ARGCHO_LOG_LEVEL_VERBOSE2 = 'VERBOSE2'
ARGCHO_LOG_LEVEL_VERBOSE1 = 'VERBOSE1'
ARGCHO_LOG_LEVEL_VERBOSE = 'VERBOSE'
ARGCHO_LOG_LEVEL_INFO = 'INFO'
ARGCHO_LOG_LEVEL_WARNING = 'WARNING'
ARGCHO_LOG_LEVEL_ERROR = 'ERROR'
ARGCHO_LOG_LEVEL_CRITICAL = 'CRITICAL'
ARGCHO_LOG_LEVEL = [
    ARGCHO_LOG_LEVEL_TRACE,
    ARGCHO_LOG_LEVEL_DEBUG,
    ARGCHO_LOG_LEVEL_INFO,
    ARGCHO_LOG_LEVEL_WARNING,
    ARGCHO_LOG_LEVEL_ERROR,
    ARGCHO_LOG_LEVEL_CRITICAL
]
# Argument choice object mapping (dict of "ARGCHO_" argument options)
ARGMAP_LOG_LEVEL = {
    ARGCHO_LOG_LEVEL_TRACE: LEVEL_TRACE,
    ARGCHO_LOG_LEVEL_DEBUG: LEVEL_DEBUG,
    ARGCHO_LOG_LEVEL_VERBOSE3: LEVEL_VERBOSE3,
    ARGCHO_LOG_LEVEL_VERBOSE2: LEVEL_VERBOSE2,
    ARGCHO_LOG_LEVEL_VERBOSE1: LEVEL_VERBOSE1,
    ARGCHO_LOG_LEVEL_VERBOSE: LEVEL_VERBOSE1,
    ARGCHO_LOG_LEVEL_INFO: LEVEL_INFO,
    ARGCHO_LOG_LEVEL_WARNING: LEVEL_WARNING,
    ARGCHO_LOG_LEVEL_ERROR: LEVEL_ERROR,
    ARGCHO_LOG_LEVEL_CRITICAL: LEVEL_CRITICAL
}
ARGCHO_LOG_MODE_APPEND = 'append'
ARGCHO_LOG_MODE_OVERWRITE = 'overwrite'
ARGCHO_LOG_MODE = [
    ARGCHO_LOG_MODE_APPEND,
    ARGCHO_LOG_MODE_OVERWRITE
]
# Argument choice object mapping (dict of "ARGCHO_" argument options)
ARGMAP_LOG_MODE_FH_MODE = {
    ARGCHO_LOG_MODE_APPEND: 'a',
    ARGCHO_LOG_MODE_OVERWRITE: 'w'
}

## Argument choice groups
ARGCHOGRP_LOG_LEVEL_STDOUT = [
    ARGCHO_LOG_LEVEL_TRACE,
    ARGCHO_LOG_LEVEL_DEBUG,
    ARGCHO_LOG_LEVEL_VERBOSE3,
    ARGCHO_LOG_LEVEL_VERBOSE2,
    ARGCHO_LOG_LEVEL_VERBOSE1,
    ARGCHO_LOG_LEVEL_VERBOSE,
    ARGCHO_LOG_LEVEL_INFO
]
ARGCHOGRP_LOG_LEVEL_STDERR = [
    ARGCHO_LOG_LEVEL_WARNING,
    ARGCHO_LOG_LEVEL_ERROR,
    ARGCHO_LOG_LEVEL_CRITICAL
]

## Argument settings
ARGSET_FLAGS = [
    (ARGSTR_LOG_APPEND, [
        (ARGSTR_LOG_MODE, ARGCHO_LOG_MODE_APPEND)
    ]),
    (ARGSTR_LOG_OVERWRITE, [
        (ARGSTR_LOG_MODE, ARGCHO_LOG_MODE_OVERWRITE)
    ]),
]

## Argument defaults ("ARGDEF_")
ARGDEF_LOG_LEVEL = ARGCHO_LOG_LEVEL_INFO
ARGDEF_LOG_TASK_LEVEL = ARGCHO_LOG_LEVEL_INFO
ARGDEF_LOG_MODE = ARGCHO_LOG_MODE_APPEND

##############################

### Custom globals ###

PSUTILS_LOGGER = logging.getLogger(__name__)
PSUTILS_LOGGER.setLevel(logging.INFO)
WARNING_LOGGER = logging.getLogger('py.warnings')
WARNING_LOGGER.setLevel(logging.INFO)
PSUTILS_LOGGER_LIST = [PSUTILS_LOGGER, WARNING_LOGGER]
LOGFMT_BASIC = logging.Formatter("%(asctime)s :: %(levelname)s -- %(message)s")
LOGFMT_DEEP = logging.Formatter("%(asctime)s (PID %(process)d) :: %(pathname)s:%(lineno)s :: %(levelname)s -- %(message)s")

LOG_STREAM_CHOICES = (sys.stdout, sys.stderr)

##############################


def add_logging_arguments(parser,
                          argdef_log_outfile=None,
                          argdef_log_errfile=None,
                          argdef_log_task_outext=None,
                          argdef_log_task_errext=None,
                          argdef_log_outdir=None,
                          argdef_log_level=ARGDEF_LOG_LEVEL,
                          argdef_log_task_level=ARGDEF_LOG_TASK_LEVEL,
                          argdef_log_mode=ARGDEF_LOG_MODE):

    parser.add_argument(
        '-ll', ARGSTR_LOG_LEVEL,
        type=functools.partial(str.upper),
        choices=ARGCHO_LOG_LEVEL,
        default=argdef_log_level,
        help=' '.join([
            "Lowest level of logging messages recorded in {} and {} log files.".format(ARGSTR_LOG_OUTFILE, ARGSTR_LOG_ERRFILE),
            "'{}' is the absolute lowest level, and '{}' is the absolute highest level.".format(
                ARGCHO_LOG_LEVEL_DEBUG, ARGCHO_LOG_LEVEL_CRITICAL
            )
        ])
    )
    parser.add_argument(
        '-ltl', ARGSTR_LOG_TASK_LEVEL,
        type=functools.partial(str.upper),
        choices=ARGCHO_LOG_LEVEL,
        default=argdef_log_task_level,
        help=' '.join([
            "Lowest level of logging messages recorded in per-task log files.",
            "'{}' is the absolute lowest level, and '{}' is the absolute highest level.".format(
                ARGCHO_LOG_LEVEL_DEBUG, ARGCHO_LOG_LEVEL_CRITICAL
            )
        ])
    )
    parser.add_argument(
        '-lo', ARGSTR_LOG_OUTFILE,
        type=psu_at.ARGTYPE_PATH(argstr=ARGSTR_LOG_OUTFILE,
            existcheck_fn=os.path.isdir,
            existcheck_reqval=False,
            accesscheck_reqtrue=os.W_OK,
            accesscheck_parent_if_dne=True),
        default=argdef_log_outfile,
        help=' '.join([
            "Path to textfile where all output log messages will be recorded.",
            "If {} is also provided, this textfile will only record stdout-type log messages {}.".format(
                ARGSTR_LOG_ERRFILE, ARGCHOGRP_LOG_LEVEL_STDOUT),
        ])
    )
    parser.add_argument(
        '-le', ARGSTR_LOG_ERRFILE,
        type=psu_at.ARGTYPE_PATH(argstr=ARGSTR_LOG_ERRFILE,
            existcheck_fn=os.path.isdir,
            existcheck_reqval=False,
            accesscheck_reqtrue=os.W_OK,
            accesscheck_parent_if_dne=True),
        default=argdef_log_errfile,
        help=' '.join([
            "Path to textfile where all stderr-type log messages {} will be recorded.".format(ARGCHOGRP_LOG_LEVEL_STDERR),
        ])
    )
    parser.add_argument(
        '-ltox', ARGSTR_LOG_TASK_OUTEXT,
        type=str,
        default=argdef_log_task_outext,
        help=' '.join([
            "File extension appended to each task source item path to determine the textfile where",
            "all output log messages from that task will be recorded.",
            "If {} is also provided, this textfile will only record stdout-type log messages {}.".format(
                ARGSTR_LOG_ERRFILE, ARGCHOGRP_LOG_LEVEL_STDOUT),
        ])
    )
    parser.add_argument(
        '-ltex', ARGSTR_LOG_TASK_ERREXT,
        type=str,
        default=argdef_log_task_errext,
        help=' '.join([
            "File extension appended to each task source item path to determine the textfile where",
            "all stderr-type log messages {} from that task will be recorded.".format(ARGCHOGRP_LOG_LEVEL_STDERR),
        ])
    )
    parser.add_argument(
        '-ltd', ARGSTR_LOG_TASK_OUTDIR,
        type=psu_at.ARGTYPE_PATH(argstr=ARGSTR_LOG_TASK_OUTDIR,
            existcheck_fn=os.path.isfile,
            existcheck_reqval=False,
            accesscheck_reqtrue=os.W_OK,
            accesscheck_parent_if_dne=True),
        default=argdef_log_outdir,
        help=' '.join([
            "Path to single directory where all task output log textfiles will be written,",
            "instead of having each task log textfile be written alongside the task source item location.",
        ])
    )
    parser.add_argument(
        '-lm', ARGSTR_LOG_MODE,
        type=str,
        choices=ARGCHO_LOG_MODE,
        default=argdef_log_mode,
        help="Method for writing new log messages to existing log files."
    )
    parser.add_argument(
        '-la', ARGSTR_LOG_APPEND,
        action='store_true',
        help="Append logging messages to existing log files."
    )
    parser.add_argument(
        '-lw', ARGSTR_LOG_OVERWRITE,
        action='store_true',
        help="Overwrite existing log files."
    )


def capture_python_warnings(capture):
    logging.captureWarnings(capture)

def get_logger_list(loggers=None):
    if loggers is None:
        logger_list = PSUTILS_LOGGER_LIST
    elif type(loggers) in (tuple, list):
        logger_list = loggers
    else:
        logger_list = [loggers]
    return logger_list

def get_logger_level(logger=None):
    if logger is None:
        logger = PSUTILS_LOGGER
    return logger.level

def set_logger_level(level, loggers=None):
    for logger in get_logger_list(loggers):
        logger.setLevel(level)

def has_handler_type(handler_type, loggers=None):
    for logger in get_logger_list(loggers):
        for handler in logger.handlers:
            if type(handler) is handler_type:
                return True
    return False

def set_handler_level(level, handler_types=None, loggers=None):
    if handler_types is None:
        handler_type_list = None
    elif type(handler_types) in (tuple, list):
        handler_type_list = handler_types
    else:
        handler_type_list = [handler_types]
    for logger in get_logger_list(loggers):
        for handler in logger.handlers:
            if handler_type_list is None or type(handler) in handler_type_list:
                handler.setLevel(level)

def set_stream_handler_level(level, loggers=None):
    set_handler_level(level, logging.StreamHandler, loggers)

def set_file_handler_level(level, loggers=None):
    set_handler_level(level, logging.FileHandler, loggers)

def remove_handlers(handler_types=None, loggers=None):
    if type(handler_types) in (tuple, list):
        handler_type_list = handler_types
    else:
        handler_type_list = [handler_types]
    for logger in get_logger_list(loggers):
        if handler_types is None:
            logger.handlers = []
            continue
        handlers_filtered = []
        for handler in logger.handlers:
            if type(handler) not in handler_type_list:
                handlers_filtered.append(handler)
        logger.handlers = handlers_filtered


class LoggerDebugFilter(logging.Filter):
    def filter(self, rec):
        return rec.levelno <= logging.DEBUG

class LoggerInfoFilter(logging.Filter):
    def filter(self, rec):
        return logging.DEBUG < rec.levelno < logging.WARNING


def setup_logging(logger=None, logger_level=None, handler_level=0, log_format=None,
                  stream_out=sys.stdout, stream_err=sys.stderr, stream_dup_err_in_out=False,
                  file_out=None, file_err=None, file_dup_err_in_out=False,
                  file_handler_mode='a',
                  capture_warnings=None,
                  remove_stream_handlers=False, remove_file_handlers=False, remove_all_handlers=False):
    new_handlers = []

    if logger_level is not None:
        set_logger_level(logger_level, logger)

    remove_existing_handlers = []
    if remove_all_handlers:
        remove_existing_handlers = None
    else:
        if remove_stream_handlers:
            remove_existing_handlers.append(logging.StreamHandler)
        if remove_file_handlers:
            remove_existing_handlers.append(logging.FileHandler)
    if remove_existing_handlers != []:
        remove_handlers(remove_existing_handlers, logger)

    add_stream_handlers = (not has_handler_type(logging.StreamHandler, logger))

    if logger is None:
        logger = PSUTILS_LOGGER
    if logger_level is None:
        logger_level = logger.level

    for file_path in [file_out, file_err]:
        if file_path is not None:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

    output_fh_items = []
    if add_stream_handlers and stream_out is not None:
        output_fh_items.append(stream_out)
    if file_out is not None:
        output_fh_items.append(file_out)

    error_fh_items = []
    if add_stream_handlers and stream_err is not None:
        error_fh_items.append(stream_err)
    if add_stream_handlers and stream_dup_err_in_out and stream_out is not None:
        error_fh_items.append(stream_out)
    if file_err is not None:
        error_fh_items.append(file_err)
    if file_dup_err_in_out and file_out is not None:
        error_fh_items.append(file_out)

    for item in output_fh_items:

        # if logger_level <= logging.DEBUG:
        debug_handler = logging.StreamHandler(item) if item in LOG_STREAM_CHOICES else logging.FileHandler(item, mode=file_handler_mode)
        debug_handler.setLevel(0)
        debug_handler.setFormatter(LOGFMT_DEEP if log_format is None else log_format)
        debug_handler.addFilter(LoggerDebugFilter())
        logger.addHandler(debug_handler)
        new_handlers.append(debug_handler)

        # if logger_level < logging.WARNING:
        info_handler = logging.StreamHandler(item) if item in LOG_STREAM_CHOICES else logging.FileHandler(item, mode=file_handler_mode)
        info_handler.setLevel(logging.DEBUG + 1 if handler_level <= logging.DEBUG else handler_level)
        info_handler.setFormatter(LOGFMT_BASIC if log_format is None else log_format)
        info_handler.addFilter(LoggerInfoFilter())
        logger.addHandler(info_handler)
        new_handlers.append(info_handler)

    for item in error_fh_items:

        warn_handler = logging.StreamHandler(item) if item in LOG_STREAM_CHOICES else logging.FileHandler(item, mode=file_handler_mode)
        warn_handler.setLevel(logging.WARNING)
        warn_handler.setFormatter(LOGFMT_DEEP if log_format is None else log_format)
        WARNING_LOGGER.addHandler(warn_handler)
        new_handlers.append(warn_handler)

        error_handler = logging.StreamHandler(item) if item in LOG_STREAM_CHOICES else logging.FileHandler(item, mode=file_handler_mode)
        error_handler.setLevel(logging.WARNING if handler_level <= logging.WARNING else handler_level)
        error_handler.setFormatter(LOGFMT_DEEP if log_format is None else log_format)
        logger.addHandler(error_handler)
        new_handlers.append(error_handler)

    if capture_warnings is True and len(WARNING_LOGGER.handlers) > 0:
        capture_python_warnings(True)
    elif capture_warnings is False:
        capture_python_warnings(False)

    return new_handlers


def setup_log_files(logger=None, logger_level=None, handler_level=0, log_format=None,
                    file_out=None, file_err=None, file_dup_err_in_out=False,
                    file_handler_mode='a',
                    capture_warnings=None,
                    remove_file_handlers=False):
    setup_logging(logger=logger, logger_level=logger_level, handler_level=handler_level, log_format=log_format,
                  stream_out=None, stream_err=None, stream_dup_err_in_out=False,
                  file_out=file_out, file_err=file_err, file_dup_err_in_out=file_dup_err_in_out,
                  file_handler_mode=file_handler_mode,
                  capture_warnings=capture_warnings,
                  remove_stream_handlers=False, remove_file_handlers=remove_file_handlers, remove_all_handlers=False)
