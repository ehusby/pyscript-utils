
import functools
import logging
import os
import sys

import psutils.argtype as psu_at


class LoggerDebugFilter(logging.Filter):
    def filter(self, rec):
        return rec.levelno == logging.DEBUG

class LoggerInfoFilter(logging.Filter):
    def filter(self, rec):
        return rec.levelno == logging.INFO


PSUTILS_LOGGER = logging.getLogger(__name__)
PSUTILS_LOGGER.setLevel(logging.DEBUG)
LOGFMT_BASIC = logging.Formatter("%(asctime)s :: %(levelname)s -- %(message)s")
LOGFMT_DEEP = logging.Formatter("%(asctime)s (PID %(process)d) :: %(pathname)s:%(lineno)s :: %(levelname)s -- %(message)s")


def setup_logging(logger=None, logger_level=None, handler_level=logging.DEBUG, log_format=None,
                  outfile=None, errfile=None, dup_err_in_outfile=False,
                  capture_warnings=None):
    if logger is None:
        logger = PSUTILS_LOGGER
    if logger_level is not None:
        logger.setLevel(logger_level)

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
        warn_logger.setLevel(handler_level)
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

    if handler_level <= logging.DEBUG:
        debug_handler = logging.StreamHandler(sys.stdout) if outfile is None else logging.FileHandler(outfile)
        debug_handler.setLevel(logging.DEBUG)
        debug_handler.setFormatter(LOGFMT_DEEP if log_format is None else log_format)
        debug_handler.addFilter(LoggerDebugFilter())
        logger.addHandler(debug_handler)

    if handler_level <= logging.INFO:
        info_handler = logging.StreamHandler(sys.stdout) if outfile is None else logging.FileHandler(outfile)
        info_handler.setLevel(logging.INFO)
        info_handler.setFormatter(LOGFMT_BASIC if log_format is None else log_format)
        info_handler.addFilter(LoggerInfoFilter())
        logger.addHandler(info_handler)

    for file in error_fh_files:
        error_handler = logging.StreamHandler(sys.stderr) if file is None else logging.FileHandler(file)
        error_handler.setLevel(logging.WARNING if handler_level <= logging.WARNING else handler_level)
        error_handler.setFormatter(LOGFMT_DEEP if log_format is None else log_format)
        logger.addHandler(error_handler)


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
ARGCHO_LOG_LEVEL_DEBUG = 'DEBUG'
ARGCHO_LOG_LEVEL_INFO = 'INFO'
ARGCHO_LOG_LEVEL_WARNING = 'WARNING'
ARGCHO_LOG_LEVEL_ERROR = 'ERROR'
ARGCHO_LOG_LEVEL_CRITICAL = 'CRITICAL'
ARGCHO_LOG_LEVEL = [
    ARGCHO_LOG_LEVEL_DEBUG,
    ARGCHO_LOG_LEVEL_INFO,
    ARGCHO_LOG_LEVEL_WARNING,
    ARGCHO_LOG_LEVEL_ERROR,
    ARGCHO_LOG_LEVEL_CRITICAL
]
# Argument choice object mapping (dict of "ARGCHO_" argument options)
ARGMAP_LOG_LEVEL_LOGGING_FUNC = {
    ARGCHO_LOG_LEVEL_DEBUG: logging.DEBUG,
    ARGCHO_LOG_LEVEL_INFO: logging.INFO,
    ARGCHO_LOG_LEVEL_WARNING: logging.WARNING,
    ARGCHO_LOG_LEVEL_ERROR: logging.ERROR,
    ARGCHO_LOG_LEVEL_CRITICAL: logging.CRITICAL
}
ARGCHO_LOG_MODE_APPEND = 'append'
ARGCHO_LOG_MODE_OVERWRITE = 'overwrite'
ARGCHO_LOG_MODE = [
    ARGCHO_LOG_MODE_APPEND,
    ARGCHO_LOG_MODE_OVERWRITE
]

## Argument choice groups
ARGCHOGRP_LOG_LEVEL_STDOUT = [
    ARGCHO_LOG_LEVEL_DEBUG,
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


def add_logging_arguments(parser,
                          argdef_log_outfile=None,
                          argdef_log_errfile=None,
                          argdef_log_task_outext=None,
                          argdef_log_task_errext=None,
                          argdef_log_outdir=None,
                          argdef_log_level=ARGCHO_LOG_LEVEL_INFO,
                          argdef_log_task_level=ARGCHO_LOG_LEVEL_INFO,
                          argdef_log_mode=ARGCHO_LOG_MODE_APPEND):

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
