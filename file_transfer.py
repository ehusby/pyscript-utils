
# Erik Husby; Polar Geospatial Center, University of Minnesota; 2020


from __future__ import print_function
from __future__ import division
import argparse
import copy
import os
import sys
import traceback

##############################

### Core globals ###

# Version numbers support multiple dot notation
SCRIPT_VERSION_NUM = "1.0"
PYTHON_VERSION_ACCEPTED_MIN = "2.7"

# Script paths and execution
SCRIPT_FILE = os.path.abspath(os.path.realpath(__file__))
SCRIPT_FNAME = os.path.basename(SCRIPT_FILE)
SCRIPT_NAME, SCRIPT_EXT = os.path.splitext(SCRIPT_FNAME)
SCRIPT_DIR = os.path.dirname(SCRIPT_FILE)
SCRIPT_RUNCMD = ' '.join(sys.argv)+'\n'
PYTHON_EXE = 'python -u'

try:
    # Look for PSU alongside script when developing
    import psutils
except ModuleNotFoundError:
    # Look for PSU repo alongside script directory
    sys.path.append(os.path.join(SCRIPT_DIR, '..', 'pyscript-utils'))
    import psutils
import psutils.custom_errors as cerr
import psutils.globals as psu_globals
from psutils.versionstring import VersionString

SCRIPT_VERSION_NUM = VersionString(SCRIPT_VERSION_NUM)
if psu_globals.PYTHON_VERSION < VersionString(PYTHON_VERSION_ACCEPTED_MIN):
    raise cerr.VersionError("Python version ({}) is below accepted minimum ({})".format(
        psu_globals.PYTHON_VERSION, PYTHON_VERSION_ACCEPTED_MIN))

##############################

### PSU imports ###

from psutils.print_methods_logging import *
from psutils.argumentpasser import RawTextArgumentDefaultsHelpFormatter

import psutils.logger as psu_log
import psutils.argtype as psu_at
import psutils.script_action as psu_act

import psutils.scheduler as psu_sched
import psutils.tasklist as psu_tl

import psutils.copymethod as psu_cm
import psutils.string as psu_str

##############################

### Script imports ###

## Python Standard Library
import glob
import logging

## Non-Standard PyPI

## Non-PyPI
from psutils.walk import WalkObject

##############################

### Argument globals ###

## Argument strings ("ARGSTR_")
# (positional first, then optional with '--' prefix)
ARGSTR_SRC_POS = 'src'
ARGSTR_DST_POS = 'dst'
ARGSTR_SRC = '--src'
ARGSTR_SRCLIST = '--srclist'
ARGSTR_SRCLIST_ROOTED = '--srclist-rooted'
ARGSTR_SRCLIST_PREFIX = '--srclist-prefix'
ARGSTR_SRCLIST_PREFIX_DST = '--srclist-prefix-dst'
ARGSTR_DST = '--dst'
ARGSTR_DSTDIR_GLOBAL = '--dstdir-global'
ARGSTR_COPY_METHOD = '--copy-method'
ARGSTR_OVERWRITE = '--overwrite'
ARGSTR_MINDEPTH = '--mindepth'
ARGSTR_MAXDEPTH = '--maxdepth'
ARGSTR_DMATCH_MAXDEPTH = '--dmatch-maxdepth'
ARGSTR_SYNC_TREE = '--sync-tree'
ARGSTR_TRANSPLANT_TREE = '--transplant-tree'
ARGSTR_COLLAPSE_TREE = '--collapse-tree'
ARGSTR_SYMLINK_FILES = '--symlink-files'
ARGSTR_FMATCH = '--fmatch'
ARGSTR_FMATCH_RE = '--fmatch-re'
ARGSTR_FEXCL = '--fexcl'
ARGSTR_FEXCL_RE = '--fexcl-re'
ARGSTR_DMATCH = '--dmatch'
ARGSTR_DMATCH_RE = '--dmatch-re'
ARGSTR_DEXCL = '--dexcl'
ARGSTR_DEXCL_RE = '--dexcl-re'
ARGSTR_SRCLIST_DELIM = '--srclist-delim'
ARGSTR_SRCLIST_NOGLOB = '--srclist-noglob'
ARGSTR_QUIET = '--quiet'
ARGSTR_DEBUG = '--debug'
ARGSTR_DRYRUN = '--dryrun'

## "Doubled" arguments
#  Optional arguments that are doubled as positional arguments for ease of use.
#  The positional arguments should not be provided if the optional arguments are provided.
DOUBLED_ARGS = {
    ARGSTR_SRC: ARGSTR_SRC_POS,
    ARGSTR_DST: ARGSTR_DST_POS,
}

## Argument groups ("ARGGRP_" lists of "ARGSTR_" argument strings)
ARGGRP_SRC = [ARGSTR_SRC, ARGSTR_SRCLIST, ARGSTR_SRCLIST_ROOTED]
ARGGRP_DST = [ARGSTR_DST, ARGSTR_DSTDIR_GLOBAL]
ARGGRP_SYNC_MODE = [ARGSTR_SYNC_TREE, ARGSTR_TRANSPLANT_TREE]
ARGGRP_FILEMATCH = [
    ARGSTR_FMATCH, ARGSTR_FMATCH_RE, ARGSTR_FEXCL, ARGSTR_FEXCL_RE,
    ARGSTR_DMATCH, ARGSTR_DMATCH_RE, ARGSTR_DEXCL, ARGSTR_DEXCL_RE,
]
ARGGRP_OUTDIR = []
ARGGRP_OUTDIR += psu_log.ARGGRP_OUTDIR  # comment-out if not using logging arguments
ARGGRP_OUTDIR += psu_sched.ARGGRP_OUTDIR  # comment-out if not using scheduler arguments

## Argument collections ("ARGCOL_" lists of "ARGGRP_" argument strings)
ARGCOL_MUT_EXCL_SET = []
ARGCOL_MUT_EXCL_SET += psu_log.ARGCOL_MUT_EXCL_SET  # comment-out if not using logging arguments
ARGCOL_MUT_EXCL_SET += [
    ARGGRP_DST,
    ARGGRP_SYNC_MODE,
    [ARGSTR_QUIET, ARGSTR_DEBUG],
    [ARGSTR_QUIET, ARGSTR_DRYRUN],
]
ARGCOL_MUT_EXCL_PROVIDED = list(ARGCOL_MUT_EXCL_SET)
ARGCOL_MUT_EXCL_PROVIDED += psu_log.ARGCOL_MUT_EXCL_PROVIDED  # comment-out if not using logging arguments

## Doubled argument restricted optional argument groups
DOUBLED_ARGS_RESTRICTED_OPTGRP = {
    'source': ARGGRP_SRC,
    'destination': ARGGRP_DST,
}

## Argument modes ("ARGMOD_", used for mutually exclusive arguments that control the same mechanic)
# (It's generally better to use a single argument with multiple choices, but sometimes we want
#  to use multiple `action='store_true'` arguments instead.)
ARGMOD_SYNC_MODE_NULL = 0
ARGMOD_SYNC_MODE_SYNC_TREE = 1
ARGMOD_SYNC_MODE_TRANSPLANT_TREE = 2

## Argument choices (declare "ARGCHO_{ARGSTR}_{option}" options followed by list of all options as "ARGCHO_{ARGSTR}")
ARGCHO_COPY_METHOD_COPY = 'copy'
ARGCHO_COPY_METHOD_MOVE = 'move'
ARGCHO_COPY_METHOD_LINK = 'link'
ARGCHO_COPY_METHOD_SYMLINK = 'symlink'
ARGCHO_COPY_METHOD = [
    ARGCHO_COPY_METHOD_COPY,
    ARGCHO_COPY_METHOD_MOVE,
    ARGCHO_COPY_METHOD_LINK,
    ARGCHO_COPY_METHOD_SYMLINK
]
# Argument choice object mapping ("ARGMAP_" dict of "ARGCHO_" argument options)
ARGMAP_COPY_METHOD_FUNC = {
    ARGCHO_COPY_METHOD_COPY: psu_cm.COPY_METHOD_COPY_DEFAULT,
    ARGCHO_COPY_METHOD_MOVE: psu_cm.COPY_METHOD_MOVE,
    ARGCHO_COPY_METHOD_LINK: psu_cm.COPY_METHOD_HARDLINK,
    ARGCHO_COPY_METHOD_SYMLINK: psu_cm.COPY_METHOD_SYMLINK
}

## Segregation of argument choices (lists of related argument choices)

## Argument settings
ARGSET_FLAGS = []
ARGSET_FLAGS += psu_log.ARGSET_FLAGS
ARGSET_CHOICES = []

## Argument defaults ("ARGDEF_")
ARGDEF_MINDEPTH = 0
ARGDEF_MAXDEPTH = psu_at.ARGNUM_POS_INF
ARGDEF_DMATCH_MAXDEPTH = psu_at.ARGNUM_POS_INF
ARGDEF_BUNDLEDIR = os.path.join(os.path.expanduser('~'), 'scratch', 'task_bundles')
ARGDEF_SRCLIST_DELIM = ','
ARGDEF_JOB_ABBREV = 'Copy'
ARGDEF_JOB_WALLTIME_HR = 1
ARGDEF_JOB_MEMORY_GB = 5

## Argument help info ("ARGHLP_", only when needed outside of argparse)
ARGHLP_SRCLIST_FORMAT = None  # set globally in pre_argparse()
ARGHLP_SRCLIST_ROOTED_FORMAT = None  # set globally in pre_argparse()

##############################

### Logging argument defaults ###

ARGDEF_LOG_LEVEL = psu_log.ARGCHO_LOG_LEVEL_INFO
ARGDEF_LOG_TASK_LEVEL = psu_log.ARGCHO_LOG_LEVEL_INFO
ARGDEF_LOG_OUTFILE = None
ARGDEF_LOG_ERRFILE = None
ARGDEF_LOG_TASK_OUTEXT = None
ARGDEF_LOG_TASK_ERREXT = None
ARGDEF_LOG_OUTDIR = None

### Scheduler settings ###

BUNDLE_TASK_ARGSTRS = [ARGSTR_SRC, ARGSTR_DST]
BUNDLE_LIST_ARGSTR = ARGSTR_SRCLIST
BUNDLE_LIST_DESCR = 'srclist'

##############################

### Custom globals ###

PATH_SEPARATORS_LIST = psu_globals.PATH_SEPARATORS_LIST
PATH_SEPARATORS_CAT = ''.join(PATH_SEPARATORS_LIST)

SYNC_MODE_GLOBAL = None

PATH_TYPE_UNKNOWN = 0
PATH_TYPE_FILE = 1
PATH_TYPE_DIR = 2
PATH_TYPE_DNE = 3

##############################

### Custom errors ###

class MetaReadError(Exception):
    def __init__(self, msg=""):
        super(Exception, self).__init__(msg)

##############################


def pre_argparse():
    global ARGHLP_SRCLIST_FORMAT, ARGHLP_SRCLIST_ROOTED_FORMAT

    provided_srclist_delimiter = psu_act.get_script_arg_values(ARGSTR_SRCLIST_DELIM)
    srclist_delimiter = provided_srclist_delimiter if provided_srclist_delimiter is not None else ARGDEF_SRCLIST_DELIM

    ARGHLP_SRCLIST_FORMAT = ' '.join([
        "\n(1) All 'src_path' line items (only when argument {}/{} directory is provided)".format(ARGSTR_DST, ARGSTR_DSTDIR_GLOBAL),
        "\n(2) A single 'src_path{}dst_dir' line at top followed by all 'src_path' line items".format(srclist_delimiter),
        "(where 'dst_dir' is a directory used for all items in the list)",
        "\n(3) All 'src_path{}dst_path' line items".format(srclist_delimiter)
    ])

    ARGHLP_SRCLIST_ROOTED_FORMAT = ' '.join([
        "A header line is expected containing 'src_rootdir[{}dst_rootdir]' to signify that".format(srclist_delimiter),
        "the folder structure from 'src_rootdir' down to 'src_path' for each 'src_path[{}dst_rootdir]'".format(srclist_delimiter),
        "line item will be replicated within the destination root directory.",
        "\nIf 'src_path' items are absolute paths, each is expected to start with the",
        "'src_rootdir' path EXACTLY as it appears in the header. If a 'src_path' item does not",
        "start with 'src_rootdir', then the 'src_path' item will be treated as a relative path",
        "within 'src_rootdir'.",
    ])


def argparser_init():
    global ARGHLP_SRCLIST_FORMAT, ARGHLP_SRCLIST_ROOTED_FORMAT

    parser = argparse.ArgumentParser(
        # formatter_class=RawTextArgumentDefaultsHelpFormatter,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        # allow_abbrev=False,
        description=' '.join([
            "Copy, link, or move a single file/directory, whole file tree, or list of files/directories.",
        ])
    )

    ## Positional arguments

    parser.add_argument(
        ARGSTR_SRC_POS,
        type=psu_at.ARGTYPE_PATH(argstr=ARGSTR_SRC_POS,
            existcheck_fn=os.path.exists,
            existcheck_reqval=True,
            accesscheck_reqtrue=os.R_OK),
        nargs='+',
        action='append',
        help=' '.join([
            "Path to source file or directory to be copied.",
        ])
    )

    parser.add_argument(
        ARGSTR_DST_POS,
        type=psu_at.ARGTYPE_PATH(argstr=ARGSTR_DST_POS,
            accesscheck_reqtrue=os.W_OK,
            accesscheck_parent_if_dne=True),
        help=' '.join([
            "Path to output file copy, or directory in which copies of source files will be created.",
        ])
    )


    ## Optional arguments

    parser.add_argument(
        '-s', ARGSTR_SRC,
        type=psu_at.ARGTYPE_PATH(argstr=ARGSTR_SRC,
            existcheck_fn=os.path.exists,
            existcheck_reqval=True,
            accesscheck_reqtrue=os.R_OK),
        nargs='+',
        action='append',
        help=' '.join([
            "Path to source file or directory to be copied.",
        ])
    )

    parser.add_argument(
        '-sl', ARGSTR_SRCLIST,
        type=psu_at.ARGTYPE_PATH(argstr=ARGSTR_SRCLIST,
            existcheck_fn=os.path.isfile,
            existcheck_reqval=True,
            accesscheck_reqtrue=os.R_OK),
        nargs='+',
        action='append',
        help=' '.join([
            "Path to output file copy, or directory in which copies of source files will be created.",
            "To provide a destination directory that overrides all destination paths in source lists,",
            "use the {} argument instead of this argument.".format(ARGSTR_DSTDIR_GLOBAL)
        ])
    )

    parser.add_argument(
        '-slr', ARGSTR_SRCLIST_ROOTED,
        type=psu_at.ARGTYPE_PATH(argstr=ARGSTR_SRCLIST_ROOTED,
            existcheck_fn=os.path.isfile,
            existcheck_reqval=True,
            accesscheck_reqtrue=os.R_OK),
        nargs='+',
        action='append',
        help=' '.join([
            "Path to textfile list of 'src_path[{}dst_rootdir]' copy tasks to be performed.".format(ARGSTR_SRCLIST_DELIM),
            ARGHLP_SRCLIST_ROOTED_FORMAT,
        ])
    )

    parser.add_argument(
        '-slp', ARGSTR_SRCLIST_PREFIX,
        type=psu_at.ARGTYPE_PATH(argstr=ARGSTR_SRCLIST_PREFIX,
            existcheck_fn=os.path.isdir,
            existcheck_reqval=True),
        help=' '.join([
            "Directory path to append to all source paths in {} copy task lists.".format(ARGSTR_SRCLIST),
        ])
    )

    parser.add_argument(
        '-slpd', ARGSTR_SRCLIST_PREFIX_DST,
        type=psu_at.ARGTYPE_PATH(argstr=ARGSTR_SRCLIST_PREFIX_DST,
            existcheck_fn=os.path.isfile,
            existcheck_reqval=False,
            accesscheck_reqtrue=os.W_OK,
            accesscheck_parent_if_dne=True),
        help=' '.join([
            "Directory path to append to all destination paths in {} copy task lists.".format(ARGSTR_SRCLIST),
        ])
    )

    parser.add_argument(
        '-d', ARGSTR_DST,
        type=psu_at.ARGTYPE_PATH(argstr=ARGSTR_DST,
            accesscheck_reqtrue=os.W_OK,
            accesscheck_parent_if_dne=True),
        help="Same as positional argument '{}'".format(ARGSTR_DST_POS),
    )
    parser.add_argument(
        '-dg', ARGSTR_DSTDIR_GLOBAL,
        type=psu_at.ARGTYPE_PATH(argstr=ARGSTR_DSTDIR_GLOBAL,
            existcheck_fn=os.path.isfile,
            existcheck_reqval=False,
            accesscheck_reqtrue=os.W_OK,
            accesscheck_parent_if_dne=True),
        help=' '.join([
            "Path to output directory in which copies of source files will be created.",
            "This destination directory will override all destination paths in source lists.",
        ])
    )

    parser.add_argument(
        '-cm', ARGSTR_COPY_METHOD,
        type=str,
        choices=ARGCHO_COPY_METHOD,
        default=ARGCHO_COPY_METHOD_LINK,
        help=' '.join([
            "Which copy method to use when performing all file transfers.",
        ])
    )
    parser.add_argument(
        '-o', ARGSTR_OVERWRITE,
        action='store_true',
        # TODO: Write help string
        help="[write me]"
    )

    parser.add_argument(
        '-d0', ARGSTR_MINDEPTH,
        type=psu_at.ARGTYPE_NUM(argstr=ARGSTR_MINDEPTH,
            numeric_type=int, allow_neg=False, allow_zero=True, allow_inf=True),
        default=ARGDEF_MINDEPTH,
        help=' '.join([
            "Minimum depth of recursive search into source directories for files to copy.",
            "\nThe depth of a source directory's immediate contents is 1.",
        ])
    )
    parser.add_argument(
        '-d1', ARGSTR_MAXDEPTH,
        type=psu_at.ARGTYPE_NUM(argstr=ARGSTR_MAXDEPTH,
            numeric_type=int, allow_neg=False, allow_zero=True, allow_inf=True),
        default=ARGDEF_MAXDEPTH,
        help=' '.join([
            "Maximum depth of recursive search into source directories for files to copy.",
            "\nThe depth of a source directory's immediate contents is 1.",
        ])
    )
    parser.add_argument(
        ARGSTR_DMATCH_MAXDEPTH,
        type=psu_at.ARGTYPE_NUM(argstr=ARGSTR_DMATCH_MAXDEPTH,
            numeric_type=int, allow_neg=False, allow_zero=True, allow_inf=True),
        default=ARGDEF_DMATCH_MAXDEPTH,
        help=' '.join([
            "[write me]",
        ])
    )

    parser.add_argument(
        '-st', ARGSTR_SYNC_TREE,
        action='store_true',
        help=' '.join([
            "Copy contents of source directories directly into destination directories."
            "\nIf neither the {} nor {} options are specified, source directory paths".format(ARGSTR_SYNC_TREE, ARGSTR_TRANSPLANT_TREE),
            "that end with '{}' are automatically treated this way.".format(PATH_SEPARATORS_LIST),
        ])
    )
    parser.add_argument(
        '-tt', ARGSTR_TRANSPLANT_TREE,
        action='store_true',
        help=' '.join([
            "Copy contents of source directories into a folder under destination directories",
            "bearing the name of the source directory (i.e. 'dstdir/srcdir_name/').",
            "\nIf neither the {} nor {} options are specified, source directory paths".format(ARGSTR_SYNC_TREE, ARGSTR_TRANSPLANT_TREE),
            "that do not end with '{}' are automatically treated this way.".format(PATH_SEPARATORS_LIST),
        ])
    )
    parser.add_argument(
        '-ct', ARGSTR_COLLAPSE_TREE,
        action='store_true',
        help=' '.join([
            "Copy all files within source directories into destination directories one level deep,"
            "effectively collapsing the copied source directory tree."
        ])
    )
    parser.add_argument(
        ARGSTR_SYMLINK_FILES,
        action='store_true',
        help=' '.join([
            "When {}={}, recurse into source folders and create symbolic links within the".format(ARGSTR_COPY_METHOD, ARGCHO_COPY_METHOD_SYMLINK),
            "destination directory pointing to the files within, instead of creating symbolic"
            "directory links within the destination pointing to source folders."
        ])
    )

    parser.add_argument(
        ARGSTR_FMATCH,
        type=str,
        nargs='+',
        action='append',
        help=' '.join([
            "[write me]",
        ])
    )
    parser.add_argument(
        ARGSTR_FMATCH_RE,
        type=str,
        nargs='+',
        action='append',
        help=' '.join([
            "[write me]",
        ])
    )
    parser.add_argument(
        ARGSTR_FEXCL,
        type=str,
        nargs='+',
        action='append',
        help=' '.join([
            "[write me]",
        ])
    )
    parser.add_argument(
        ARGSTR_FEXCL_RE,
        type=str,
        nargs='+',
        action='append',
        help=' '.join([
            "[write me]",
        ])
    )

    parser.add_argument(
        ARGSTR_DMATCH,
        type=str,
        nargs='+',
        action='append',
        help=' '.join([
            "[write me]",
        ])
    )
    parser.add_argument(
        ARGSTR_DMATCH_RE,
        type=str,
        nargs='+',
        action='append',
        help=' '.join([
            "[write me]",
        ])
    )
    parser.add_argument(
        ARGSTR_DEXCL,
        type=str,
        nargs='+',
        action='append',
        help=' '.join([
            "[write me]",
        ])
    )
    parser.add_argument(
        ARGSTR_DEXCL_RE,
        type=str,
        nargs='+',
        action='append',
        help=' '.join([
            "[write me]",
        ])
    )

    parser.add_argument(
        ARGSTR_SRCLIST_DELIM,
        type=str,
        default=ARGDEF_SRCLIST_DELIM,
        help=' '.join([
            "Delimiter used to separate source and destination paths in {} and {} textfiles.".format(ARGSTR_SRCLIST, ARGSTR_SRCLIST_ROOTED),
        ])
    )
    parser.add_argument(
        ARGSTR_SRCLIST_NOGLOB,
        action='store_true',
        help=' '.join([
            "Do not interpret '*' character as a wildcard for path-globbing in {} and {} textfiles.".format(ARGSTR_SRCLIST, ARGSTR_SRCLIST_ROOTED),
        ])
    )

    # Comment-out this block if not using scheduler arguments
    psu_sched.add_scheduler_arguments(parser,
        ARGDEF_JOB_ABBREV,
        ARGDEF_JOB_WALLTIME_HR,
        ARGDEF_JOB_MEMORY_GB,
        ARGDEF_BUNDLEDIR,
    )

    # Comment-out the following line if not using logging arguments
    psu_log.add_logging_arguments(parser)

    parser.add_argument(
        '-q', ARGSTR_QUIET,
        action='store_true',
        # TODO: Write help string
        help="[write me]"
    )
    parser.add_argument(
        '-db', ARGSTR_DEBUG,
        action='store_true',
        # TODO: Write help string
        help="[write me]"
    )
    parser.add_argument(
        '-dr', ARGSTR_DRYRUN,
        action='store_true',
        help="Print actions without executing."
    )

    return parser


def main():
    global SYNC_MODE_GLOBAL
    # from psutils.print_methods_logging import *

    ### Parse script arguments
    pre_argparse()
    arg_parser = argparser_init()
    args = psu_act.parse_args(PYTHON_EXE, SCRIPT_FILE, arg_parser, sys.argv,
                              DOUBLED_ARGS, DOUBLED_ARGS_RESTRICTED_OPTGRP)
    ### Setup logging
    psu_log.PSUTILS_LOGGER.handlers = []
    psu_log.setup_logging(handler_level=(logging.DEBUG if args.get(ARGSTR_DEBUG) else logging.INFO))
    psu_act.setup_outfile_logging(args)
    logging_level_task = psu_log.ARGMAP_LOG_LEVEL_LOGGING_FUNC[args.get(psu_log.ARGSTR_LOG_TASK_LEVEL)]

    ### Apply usual argument adjustments
    psu_act.apply_argument_settings(args, ARGSET_FLAGS, ARGSET_CHOICES)
    psu_act.set_default_jobscript(args)


    ### Further parse/adjust script argument values

    ## Restructure provided source arguments into flat lists
    psu_act.flatten_nargs_plus_action_append_lists(args, ARGGRP_SRC, ARGGRP_FILEMATCH)


    ## Print script preamble when done adjusting argument values
    script_preamble = psu_act.get_preamble(args, sys.argv)
    if args.get(ARGSTR_DEBUG):
        print(script_preamble)
    if args.get(psu_log.ARGSTR_LOG_OUTFILE) is not None:
        with open(args.get(psu_log.ARGSTR_LOG_OUTFILE), 'a') as fp_outlog:
            print(script_preamble, file=fp_outlog)


    ### Validate argument values

    psu_act.check_mutually_exclusive_args(args, ARGCOL_MUT_EXCL_SET, ARGCOL_MUT_EXCL_PROVIDED)

    arg_dst = args.get(ARGSTR_DST) if args.get(ARGSTR_DST) is not None else args.get(ARGSTR_DSTDIR_GLOBAL)
    arg_srclist_prefix = args.get(ARGSTR_SRCLIST_PREFIX)
    arg_srclist_prefix_dst = args.get(ARGSTR_SRCLIST_PREFIX_DST)
    arg_srclist_noglob = args.get(ARGSTR_SRCLIST_NOGLOB)

    if args.get(ARGSTR_SYNC_TREE):
        SYNC_MODE_GLOBAL = ARGMOD_SYNC_MODE_SYNC_TREE
    elif args.get(ARGSTR_TRANSPLANT_TREE):
        SYNC_MODE_GLOBAL = ARGMOD_SYNC_MODE_TRANSPLANT_TREE
    else:
        SYNC_MODE_GLOBAL = ARGMOD_SYNC_MODE_NULL

    src_list = []
    srclist_tasklists = []
    srclist_rooted_tasklists = []

    ## Parse and validate multiple source arguments

    if args.get(ARGSTR_SRC):
        if arg_dst is None:
            arg_parser.error("argument {}/{} is required when {} is provided".format(
                ARGSTR_DST, ARGSTR_DSTDIR_GLOBAL, ARGSTR_SRC))
        src_list.extend(args.get(ARGSTR_SRC))

    if args.get(ARGSTR_SRCLIST):
        for srclist_file in args.get(ARGSTR_SRCLIST):
            try:
                if arg_dst is None:
                    srclist_header = psu_tl.read_task_bundle(
                        srclist_file, ncol_min=1, ncol_max=2,
                        header_rows=1, read_header=True,
                        args_delim=args.get(ARGSTR_SRCLIST_DELIM)
                    )
                    if len(srclist_header) == 0:
                        continue
                    elif len(srclist_header) != 2:
                        raise cerr.DimensionError
                tasklist = psu_tl.Tasklist(
                    srclist_file, ncol_min=1, ncol_max=2, ncol_strict=True, ncol_strict_header_separate=True,
                    header_rows=1,
                    args_delim=args.get(ARGSTR_SRCLIST_DELIM)
                )
                if len(tasklist.header) == 0:
                    tasklist.header = None
                elif len(tasklist.tasks) == 0:
                    tasklist.tasks = [tasklist.header]
                    tasklist.header = None
                elif len(tasklist.tasks) > 0:
                    if len(tasklist.header) == 1:
                        if type(tasklist.tasks[0]) is list and len(tasklist.tasks[0]) == 2:
                            raise cerr.DimensionError
                        tasklist.tasks.insert(0, tasklist.header[0])
                        tasklist.header = None
                    elif len(tasklist.header) == 2:
                        if type(tasklist.tasks[0]) is list and len(tasklist.tasks[0]) == 2:
                            tasklist.tasks.insert(0, tasklist.header)
                            tasklist.header = None
                        elif type(tasklist.tasks[0]) is list and len(tasklist.tasks[0]) == 1:
                            tasklist.tasks.insert(0, [tasklist.header[0]])
                        else:
                            tasklist.tasks.insert(0, tasklist.header[0])
                if type(tasklist.header) is list and len(tasklist.header) == 0:
                    tasklist.header = None
            except cerr.DimensionError as e:
                traceback.print_exc()
                arg_parser.error(
                    "{} {}; {} textfiles must be structured in one of the following formats:\n{}".format(
                        ARGSTR_SRCLIST, srclist_file, ARGSTR_SRCLIST, ARGHLP_SRCLIST_FORMAT
                ))

            tasklist_src_dne = []
            task_type_is_list = (len(tasklist.tasks) > 0 and type(tasklist.tasks[0]) is list)
            for task in tasklist.tasks:
                task_src = task[0] if task_type_is_list else task
                if arg_srclist_prefix is not None:
                    task_src = os.path.join(arg_srclist_prefix, task_src)
                if (not arg_srclist_noglob and '*' in task_src) or os.path.exists(task_src):
                    pass
                else:
                    tasklist_src_dne.append(task_src)
            if len(tasklist_src_dne) > 0:
                arg_parser.error("{} {}; source paths do not exist:\n{}".format(
                    ARGSTR_SRCLIST, srclist_file, '\n'.join(tasklist_src_dne)
                ))

            if len(tasklist.tasks) > 0:
                srclist_tasklists.append(tasklist)

    if args.get(ARGSTR_SRCLIST_ROOTED):
        for srclist_file in args.get(ARGSTR_SRCLIST_ROOTED):
            try:
                if arg_dst is None:
                    srclist_first_two_lines = psu_tl.read_task_bundle(
                        srclist_file, ncol_min=1, ncol_max=2,
                        header_rows=2, read_header=True, allow_1d_task_list=False,
                        args_delim=args.get(ARGSTR_SRCLIST_DELIM)
                    )
                    if len(srclist_first_two_lines) == 0:
                        pass
                    elif 2 not in [len(line_items) for line_items in srclist_first_two_lines]:
                        raise cerr.DimensionError
                    else:
                        srclist_header = srclist_first_two_lines[0]
                        src_rootdir = srclist_header[0]
                        dst_rootdir = srclist_header[1] if len(srclist_header) == 2 else None
                        if not os.path.isdir(src_rootdir):
                            arg_parser.error(
                                "{} {}; source root directory in header must be an existing directory: {}".format(
                                ARGSTR_SRCLIST_ROOTED, srclist_file, src_rootdir
                            ))
                        if dst_rootdir is not None and os.path.isfile(dst_rootdir):
                            arg_parser.error(
                                "{} {}; destination root directory in header cannot be an existing file: {}".format(
                                ARGSTR_SRCLIST_ROOTED, srclist_file, dst_rootdir
                            ))
                tasklist = psu_tl.Tasklist(
                    srclist_file, ncol_min=1, ncol_max=2, ncol_strict=True, ncol_strict_header_separate=True,
                    header_rows=1,
                    args_delim=args.get(ARGSTR_SRCLIST_DELIM)
                )
            except cerr.DimensionError as e:
                traceback.print_exc()
                arg_parser.error("{} {}; {} textfiles must be structured as follows:\n{}".format(
                    ARGSTR_SRCLIST_ROOTED, srclist_file, ARGSTR_SRCLIST_ROOTED, ARGHLP_SRCLIST_ROOTED_FORMAT
                ))

            tasklist_src_dne = []
            task_type_is_list = (len(tasklist.tasks) > 0 and type(tasklist.tasks[0]) is list)
            for task in tasklist.tasks:
                if task_type_is_list:
                    task_src, task_dst_rootdir = task
                    if os.path.isfile(task_dst_rootdir):
                        arg_parser.error(
                            "{} {}; destination root directory cannot be an existing file: {}".format(
                            ARGSTR_SRCLIST_ROOTED, tasklist.tasklist_file, task_dst_rootdir
                        ))
                else:
                    task_src = task
                if (not arg_srclist_noglob and '*' in task_src) or os.path.exists(task_src):
                    pass
                else:
                    tasklist_src_dne.append(task_src)
            if len(tasklist_src_dne) > 0:
                arg_parser.error("{} {}; source paths do not exist:\n{}".format(
                    ARGSTR_SRCLIST_ROOTED, srclist_file, '\n'.join(tasklist_src_dne)
                ))

            if len(tasklist.tasks) > 0:
                srclist_rooted_tasklists.append(tasklist)


    arg_dst_can_be_file = False
    if args.get(ARGSTR_SRC) and args.get(ARGSTR_DST) and not os.path.isdir(args.get(ARGSTR_DST)):
        if len(src_list) == 1 and not (args.get(ARGSTR_SRCLIST) or args.get(ARGSTR_SRCLIST_ROOTED)):
            arg_dst_can_be_file = True


    ### Build list of tasks to be performed

    all_task_list = []

    ## Standardize source and destination paths to SYNC-style for file copy tasks

    for src_path in src_list:
        dst_path = arg_dst
        dst_path = adjust_dst_path(src_path, dst_path, arg_dst_can_be_file)
        all_task_list.append((src_path, dst_path))

    for tasklist in srclist_tasklists:

        tasklist_dst_can_be_file = False
        if args.get(ARGSTR_DSTDIR_GLOBAL) is not None:
            tasklist_dst_dir = args.get(ARGSTR_DSTDIR_GLOBAL)
        elif tasklist.header is not None:
            tasklist_dst_dir = tasklist.header[1]
        else:
            tasklist_dst_dir = None
            tasklist_dst_can_be_file = True

        if tasklist_dst_dir is None:
            dst_path_type = PATH_TYPE_UNKNOWN
        else:
            if not os.path.exists(tasklist_dst_dir):
                dst_path_type = PATH_TYPE_DNE
            elif os.path.isdir(tasklist_dst_dir):
                dst_path_type = PATH_TYPE_DIR
            elif os.path.isfile(tasklist_dst_dir):
                dst_path_type = PATH_TYPE_FILE
            else:
                dst_path_type = PATH_TYPE_UNKNOWN

        task_type_is_list = (len(tasklist.tasks) > 0 and type(tasklist.tasks[0]) is list)
        for task in tasklist.tasks:
            if task_type_is_list:
                src_path = task[0]
                if tasklist_dst_dir is not None:
                    dst_path = tasklist_dst_dir
                else:
                    dst_path = task[1]
                    if arg_srclist_prefix_dst is not None:
                        dst_path = os.path.join(arg_srclist_prefix_dst, dst_path)
            else:
                src_path = task
                dst_path = tasklist_dst_dir if tasklist_dst_dir is not None else arg_dst

            if arg_srclist_prefix is not None:
                src_path = os.path.join(arg_srclist_prefix, src_path)

            if not arg_srclist_noglob and '*' in src_path:
                src_path_glob = glob.glob(src_path)
                if len(src_path_glob) == 0:
                    warning("{} {}; no source files found matching pattern: {}".format(
                        ARGSTR_SRCLIST, tasklist.tasklist_file, src_path
                    ))
                for src_path in src_path_glob:
                    dst_path = adjust_dst_path(
                        src_path, dst_path, dst_can_be_file=False, dst_path_type=dst_path_type,
                        sync_mode_default=ARGMOD_SYNC_MODE_TRANSPLANT_TREE
                    )
                    all_task_list.append((src_path, dst_path))
            else:
                dst_path = adjust_dst_path(
                    src_path, dst_path, tasklist_dst_can_be_file, dst_path_type
                )
                all_task_list.append((src_path, dst_path))

    for tasklist in srclist_rooted_tasklists:

        src_rootdir = tasklist.header[0]

        if not os.path.isdir(src_rootdir):
            arg_parser.error(
                "{} {}; source root directory in header must be an existing directory: {}".format(
                ARGSTR_SRCLIST_ROOTED, tasklist.tasklist_file, src_rootdir
            ))

        if args.get(ARGSTR_DSTDIR_GLOBAL) is not None:
            tasklist_dst_rootdir = args.get(ARGSTR_DSTDIR_GLOBAL)
        elif len(tasklist.header) == 2:
            tasklist_dst_rootdir = tasklist.header[1]
        else:
            tasklist_dst_rootdir = None

        sync_mode = SYNC_MODE_GLOBAL
        if sync_mode == ARGMOD_SYNC_MODE_NULL:
            # Assume user expects the new destination directory to mirror the source directory
            sync_mode = ARGMOD_SYNC_MODE_SYNC_TREE

        src_rootdir_dirname = os.path.basename(src_rootdir.rstrip(PATH_SEPARATORS_CAT))
        if tasklist_dst_rootdir is not None and sync_mode == ARGMOD_SYNC_MODE_TRANSPLANT_TREE:
            tasklist_dst_rootdir = os.path.join(tasklist_dst_rootdir, src_rootdir_dirname)

        task_type_is_list = (len(tasklist.tasks) > 0 and type(tasklist.tasks[0]) is list)
        for task in tasklist.tasks:
            if task_type_is_list:
                src_path = task[0]
                dst_rootdir = tasklist_dst_rootdir if tasklist_dst_rootdir is not None else task[1]
            else:
                src_path = task
                dst_rootdir = tasklist_dst_rootdir if tasklist_dst_rootdir is not None else arg_dst

            if os.path.isfile(dst_rootdir):
                arg_parser.error(
                    "{} {}; destination root directory cannot be an existing file: {}".format(
                    ARGSTR_SRCLIST_ROOTED, tasklist.tasklist_file, dst_rootdir
                ))

            if not src_path.startswith(src_rootdir):
                # Assume source path is relative from the source root directory
                src_path_from_root = src_path
                src_path = os.path.join(src_rootdir, src_path_from_root)

            if not arg_srclist_noglob and '*' in src_path:
                src_path_glob = glob.glob(src_path)
                if len(src_path_glob) == 0:
                    warning("{} {}; no source files found matching pattern: {}".format(
                        ARGSTR_SRCLIST_ROOTED, tasklist.tasklist_file, src_path
                    ))
            else:
                src_path_glob = [src_path]
            for src_path in src_path_glob:

                src_path_from_root = src_path.replace(src_rootdir, '') if src_path.startswith(src_rootdir) else src_path
                if tasklist_dst_rootdir is None and sync_mode == ARGMOD_SYNC_MODE_TRANSPLANT_TREE:
                    dst_path = os.path.join(dst_rootdir, src_rootdir_dirname, src_path_from_root)
                else:
                    dst_path = os.path.join(dst_rootdir, src_path_from_root)

                all_task_list.append((src_path, dst_path))


    ### Create output directories if they don't already exist
    if not args.get(ARGSTR_DRYRUN):
        psu_act.create_argument_directories(args, *ARGGRP_OUTDIR)


    ### Perform tasks

    error_trace = None
    try:
        if args.get(psu_sched.ARGSTR_SCHEDULER) is not None:
            ## Submit tasks to scheduler
            parent_tasks = all_task_list
            parent_args = args
            child_args = copy.deepcopy(args)
            child_args.unset(psu_sched.ARGGRP_SCHEDULER)
            child_args.unset(ARGSTR_TRANSPLANT_TREE)
            child_args.set(ARGSTR_SYNC_TREE)
            psu_act.submit_tasks_to_scheduler(
                parent_args, parent_tasks,
                BUNDLE_TASK_ARGSTRS, BUNDLE_LIST_ARGSTR,
                child_args,
                task_items_descr=BUNDLE_LIST_DESCR,
                task_delim=ARGSTR_SRCLIST_DELIM,
                python_version_accepted_min=PYTHON_VERSION_ACCEPTED_MIN,
                dryrun=args.get(ARGSTR_DRYRUN)
            )
            sys.exit(0)

        ## Perform tasks in serial
        perform_tasks(args, all_task_list)

    except KeyboardInterrupt:
        raise

    except Exception as e:
        error_trace = psu_act.handle_task_exception(args, e)

    if type(args.get(psu_sched.ARGSTR_EMAIL)) is str:
        psu_act.send_script_completion_email(args, error_trace)

    sys.exit(1 if error_trace is not None else 0)


def perform_tasks(args, task_list):

    copy_method_obj = copy.copy(ARGMAP_COPY_METHOD_FUNC[args.get(ARGSTR_COPY_METHOD)])
    copy_method_obj.set_options(
        copy_overwrite=args.get(ARGSTR_OVERWRITE),
        copy_dryrun=args.get(ARGSTR_DRYRUN),
        copy_verbose=(not args.get(ARGSTR_QUIET)),
        copy_debug=args.get(ARGSTR_DEBUG)
    )

    walk_object = WalkObject(
        mindepth=args.get(ARGSTR_MINDEPTH), maxdepth=args.get(ARGSTR_MAXDEPTH), dmatch_maxdepth=args.get(ARGSTR_DMATCH_MAXDEPTH),
        fmatch=args.get(ARGSTR_FMATCH), fmatch_re=args.get(ARGSTR_FMATCH_RE),
        fexcl=args.get(ARGSTR_FEXCL), fexcl_re=args.get(ARGSTR_FEXCL_RE),
        dmatch=args.get(ARGSTR_DMATCH), dmatch_re=args.get(ARGSTR_DMATCH_RE),
        dexcl=args.get(ARGSTR_DEXCL), dexcl_re=args.get(ARGSTR_DEXCL_RE),
        copy_method=copy_method_obj, copy_overwrite=args.get(ARGSTR_OVERWRITE),
        transplant_tree=False, collapse_tree=args.get(ARGSTR_COLLAPSE_TREE),
        copy_dryrun=args.get(ARGSTR_DRYRUN), copy_quiet=args.get(ARGSTR_QUIET), copy_debug=args.get(ARGSTR_DEBUG)
    )

    for task_srcpath, task_dstpath in task_list:
        if os.path.isfile(task_srcpath):
            task_srcfile = task_srcpath
            task_dstfile = task_dstpath
            copy_method_obj.copy(task_srcfile, task_dstfile)
        else:
            task_srcdir = task_srcpath
            task_dstdir = task_dstpath
            for x in walk_object.walk(task_srcdir, task_dstdir):
                pass


def adjust_dst_path(src_path, dst_path, dst_can_be_file=False, dst_path_type=PATH_TYPE_UNKNOWN,
                    sync_mode_default=ARGMOD_SYNC_MODE_NULL):
    global SYNC_MODE_GLOBAL

    if dst_path_type == PATH_TYPE_DIR or (dst_path_type == PATH_TYPE_UNKNOWN and os.path.isdir(dst_path)):
        if os.path.isfile(src_path):
            dst_path = os.path.join(dst_path, os.path.basename(src_path))
        else:
            # src_path is a directory
            sync_mode = SYNC_MODE_GLOBAL if SYNC_MODE_GLOBAL != ARGMOD_SYNC_MODE_NULL else sync_mode_default
            if sync_mode == ARGMOD_SYNC_MODE_NULL:
                sync_mode = ARGMOD_SYNC_MODE_SYNC_TREE if psu_str.endswith_one_of_coll(src_path, PATH_SEPARATORS_LIST) else ARGMOD_SYNC_MODE_TRANSPLANT_TREE
            if sync_mode == ARGMOD_SYNC_MODE_TRANSPLANT_TREE:
                dst_path = os.path.join(dst_path, os.path.basename(src_path.rstrip(PATH_SEPARATORS_CAT)))
            if not psu_str.endswith_one_of_coll(dst_path, PATH_SEPARATORS_LIST):
                dst_path = dst_path+os.path.sep

    elif dst_path_type == PATH_TYPE_FILE or (dst_path_type == PATH_TYPE_UNKNOWN and os.path.isfile(dst_path)):
        if os.path.isdir(src_path):
            raise cerr.ScriptArgumentError(
                "source directory ({}) cannot overwrite existing destination file ({})".format(src_path, dst_path)
            )
        else:
            # src_path is a file
            pass

    else:
        # dst_path does not yet exist
        if os.path.isfile(src_path):
            if dst_can_be_file and not psu_str.endswith_one_of_coll(dst_path, PATH_SEPARATORS_LIST):
                # dst_path will be the exact path of the file copy
                pass
            else:
                dst_path = os.path.join(dst_path, os.path.basename(src_path))
        else:
            # src_path is a directory; dst_path will be a new destination directory
            sync_mode = SYNC_MODE_GLOBAL if SYNC_MODE_GLOBAL != ARGMOD_SYNC_MODE_NULL else sync_mode_default
            if sync_mode == ARGMOD_SYNC_MODE_NULL:
                # Assume user expects the new destination directory to mirror the source directory
                sync_mode = ARGMOD_SYNC_MODE_SYNC_TREE
            if sync_mode == ARGMOD_SYNC_MODE_TRANSPLANT_TREE:
                dst_path = os.path.join(dst_path, os.path.basename(src_path.rstrip(PATH_SEPARATORS_CAT)))
            if not psu_str.endswith_one_of_coll(dst_path, PATH_SEPARATORS_LIST):
                dst_path = dst_path+os.path.sep

    return dst_path



if __name__ == '__main__':
    main()
