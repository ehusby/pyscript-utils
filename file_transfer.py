
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
except ImportError:
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

### PSU standard imports ###

from psutils.print_methods_logging import *
from psutils.argumentpasser import RawTextArgumentDefaultsHelpFormatter

import psutils.logger as psu_log
import psutils.argtype as psu_at
import psutils.script_action as psu_act

import psutils.scheduler as psu_sched
import psutils.tasklist as psu_tl

import psutils.copymethod as psu_cm

##############################

### Script imports ###

## Python Standard Library
import logging

## Non-Standard PyPI
try:
    from tqdm import tqdm
except ImportError:
    pass

## Non-PyPI
from psutils.walk import WalkObject

##############################

### Argument globals ###

## Argument strings ("ARGSTR_")
# (positional first, then optional with '--' prefix)
ARGSTR_SRC_POS = 'src'
ARGSTR_DST_POS = 'dst'
ARGSTR_SRC = '--src'
ARGSTR_DST = '--dst'
ARGSTR_COPY_METHOD = '--copy-method'
ARGSTR_OVERWRITE_FILES = '--overwrite-files'
ARGSTR_OVERWRITE_DIRS = '--overwrite-dirs'
ARGSTR_OVERWRITE_DMATCH = '--overwrite-dmatch'
ARGSTR_MKDIR_UPON_FILE_COPY = '--mkdir-upon-file-copy'
ARGSTR_MINDEPTH = '--mindepth'
ARGSTR_MAXDEPTH = '--maxdepth'
ARGSTR_DMATCH_MAXDEPTH = '--dmatch-maxdepth'
ARGSTR_SYMLINK_FILES = '--symlink-files'
ARGSTR_FMATCH = '--fmatch'
ARGSTR_FMATCH_RE = '--fmatch-re'
ARGSTR_FEXCL = '--fexcl'
ARGSTR_FEXCL_RE = '--fexcl-re'
ARGSTR_DMATCH = '--dmatch'
ARGSTR_DMATCH_RE = '--dmatch-re'
ARGSTR_DEXCL = '--dexcl'
ARGSTR_DEXCL_RE = '--dexcl-re'
ARGSTR_HARDLINK_RECORDS_DIR = '--hardlink-records-dir'
ARGSTR_NO_HARDLINK_RECORDS = '--no-hardlink-records'
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
ARGGRP_SRC = [ARGSTR_SRC]
ARGGRP_SRC += psu_tl.ARGGRP_SRC  # comment-out if not using source list arguments
ARGGRP_DST = [ARGSTR_DST]
ARGGRP_DST += psu_tl.ARGGRP_DST  # comment-out if not using source list arguments
ARGGRP_FILEMATCH = [
    ARGSTR_FMATCH, ARGSTR_FMATCH_RE, ARGSTR_FEXCL, ARGSTR_FEXCL_RE,
    ARGSTR_DMATCH, ARGSTR_DMATCH_RE, ARGSTR_DEXCL, ARGSTR_DEXCL_RE,
]
ARGGRP_OUTDIR = [ARGSTR_HARDLINK_RECORDS_DIR]
ARGGRP_OUTDIR += psu_log.ARGGRP_OUTDIR  # comment-out if not using logging arguments
ARGGRP_OUTDIR += psu_sched.ARGGRP_OUTDIR  # comment-out if not using scheduler arguments

## Argument collections ("ARGCOL_" lists of "ARGGRP_" argument strings)
ARGCOL_MUT_EXCL_SET = []
ARGCOL_MUT_EXCL_SET += psu_log.ARGCOL_MUT_EXCL_SET  # comment-out if not using logging arguments
ARGCOL_MUT_EXCL_SET += [
    ARGGRP_DST,
    psu_tl.ARGGRP_SYNC_MODE,
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
# ARGMOD_SYNC_MODE_NULL = 0
# ARGMOD_SYNC_MODE_SYNC_TREE = 1
# ARGMOD_SYNC_MODE_TRANSPLANT_TREE = 2

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
ARGDEF_SRCLIST_DELIM = ','
ARGDEF_HARDLINK_RECORD_DIR = os.path.realpath(os.path.join(os.path.expanduser('~'), 'scratch', '{}_hardlink_records'.format(SCRIPT_NAME)))
ARGDEF_BUNDLEDIR = os.path.realpath(os.path.join(os.path.expanduser('~'), 'scratch', 'task_bundles'))
ARGDEF_JOB_ABBREV = 'Copy'
ARGDEF_JOB_WALLTIME_HR = 1
ARGDEF_JOB_MEMORY_GB = 5

## Argument help info ("ARGHLP_", only when needed outside of argparse)
# ARGHLP_SRCLIST_FORMAT = None  # set globally in pre_argparse()
# ARGHLP_SRCLIST_ROOTED_FORMAT = None  # set globally in pre_argparse()

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
BUNDLE_LIST_ARGSTR = psu_tl.ARGSTR_ARGLIST
BUNDLE_LIST_DESCR = 'srclist'

##############################

### Custom globals ###


##############################

### Custom errors ###

class MetaReadError(Exception):
    def __init__(self, msg=""):
        super(Exception, self).__init__(msg)

##############################


def pre_argparse():
    psu_tl.pre_argparse(ARGDEF_SRCLIST_DELIM, argstr_dst=ARGSTR_DST)


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
            "To provide a destination directory that overrides all destination paths in source lists,",
            "use the {} argument instead of this argument.".format(psu_tl.ARGSTR_DSTDIR_GLOBAL)
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
        '-d', ARGSTR_DST,
        type=psu_at.ARGTYPE_PATH(argstr=ARGSTR_DST,
            accesscheck_reqtrue=os.W_OK,
            accesscheck_parent_if_dne=True),
        help="Same as positional argument '{}'".format(ARGSTR_DST_POS),
    )

    # Comment-out this block if not using tasklist arguments
    psu_tl.add_srclist_arguments(parser,
        ARGDEF_SRCLIST_DELIM
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
        ARGSTR_OVERWRITE_FILES,
        action='store_true',
        # TODO: Write help string
        help="[write me]"
    )
    parser.add_argument(
        ARGSTR_OVERWRITE_DIRS,
        action='store_true',
        # TODO: Write help string
        help="[write me]"
    )
    parser.add_argument(
        ARGSTR_OVERWRITE_DMATCH,
        action='store_true',
        # TODO: Write help string
        help="[write me]"
    )

    parser.add_argument(
        '-mufc', ARGSTR_MKDIR_UPON_FILE_COPY,
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
        '-hrd', ARGSTR_HARDLINK_RECORDS_DIR,
        type=psu_at.ARGTYPE_PATH(argstr=ARGSTR_HARDLINK_RECORDS_DIR,
            existcheck_fn=os.path.isfile,
            existcheck_reqval=False,
            accesscheck_reqtrue=os.W_OK,
            accesscheck_parent_if_dne=True),
        default=ARGDEF_HARDLINK_RECORD_DIR,
        help=' '.join([
            "If {}={}, this is the root directory in which a mirror of the current filesystem".format(ARGSTR_COPY_METHOD, ARGCHO_COPY_METHOD_LINK),
            "will be populated with symlinks to all hardlinked destination files and directories.",
            "This is to serve as a reminder of the files and directories that have been hardlinked.",
        ])
    )
    parser.add_argument(
        '-nhr', ARGSTR_NO_HARDLINK_RECORDS,
        action='store_true',
        default=True,
        # TODO: Write help string
        help="[write me]"
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

    all_task_list = psu_tl.parse_src_args(args, ARGSTR_SRC, ARGSTR_DST)


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
            child_args.unset(psu_tl.ARGSTR_TRANSPLANT_TREE)
            child_args.set(psu_tl.ARGSTR_SYNC_TREE)
            psu_act.submit_tasks_to_scheduler(
                parent_args, parent_tasks,
                BUNDLE_TASK_ARGSTRS, BUNDLE_LIST_ARGSTR,
                child_args,
                task_items_descr=BUNDLE_LIST_DESCR,
                task_delim=psu_tl.ARGSTR_SRCLIST_DELIM,
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
        check_srcpath_exists=True,
        copy_makedirs=True,
        copy_overwrite_files=args.get(ARGSTR_OVERWRITE_FILES),
        copy_overwrite_dirs=args.get(ARGSTR_OVERWRITE_DIRS),
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
        copy_method=copy_method_obj, copy_overwrite_files=args.get(ARGSTR_OVERWRITE_FILES), copy_overwrite_dirs=args.get(ARGSTR_OVERWRITE_DIRS), copy_overwrite_dmatch=args.get(ARGSTR_OVERWRITE_DMATCH),
        symlink_dirs=(not args.get(ARGSTR_SYMLINK_FILES)),
        transplant_tree=False, collapse_tree=args.get(psu_tl.ARGSTR_COLLAPSE_TREE),
        copy_dryrun=args.get(ARGSTR_DRYRUN), copy_quiet=args.get(ARGSTR_QUIET), copy_debug=args.get(ARGSTR_DEBUG),
        mkdir_upon_file_copy=args.get(ARGSTR_MKDIR_UPON_FILE_COPY)
    )

    do_record_hardlinks = (args.get(ARGSTR_COPY_METHOD) == ARGCHO_COPY_METHOD_LINK and not args.get(ARGSTR_NO_HARDLINK_RECORDS))
    if do_record_hardlinks:
        hardlink_record_dir = args.get(ARGSTR_HARDLINK_RECORDS_DIR)
        copy_method_obj_symlink_record = copy.copy(ARGMAP_COPY_METHOD_FUNC[ARGCHO_COPY_METHOD_SYMLINK])
        copy_method_obj_symlink_record.set_options(
            copy_makedirs=True,
            copy_overwrite_files=True,
            copy_overwrite_dirs=True,
            copy_dryrun=args.get(ARGSTR_DRYRUN),
            copy_verbose=args.get(ARGSTR_DEBUG),
            copy_debug=args.get(ARGSTR_DEBUG)
        )

    # for task_srcpath, task_dstpath in tqdm(task_list):
    for task_srcpath, task_dstpath in task_list:
        if os.path.isfile(task_srcpath):
            task_srcfile = task_srcpath
            task_dstfile = task_dstpath
            copy_success = copy_method_obj.copy(task_srcfile, task_dstfile)
        else:
            task_srcdir = task_srcpath
            task_dstdir = task_dstpath
            for x in walk_object.walk(task_srcdir, task_dstdir):
                pass

        if do_record_hardlinks:
            task_dstpath_drive, task_dstpath_tail = os.path.splitdrive(os.path.realpath(task_dstpath))

            record_dstpath_for_src = os.path.normpath(
                "{}/src/{}/{}".format(
                    hardlink_record_dir,
                    task_dstpath_drive.rstrip(':'),
                    task_dstpath_tail
                )
            )
            record_dstpath_for_dst = os.path.normpath(
                "{}/dst/{}/{}".format(
                    hardlink_record_dir,
                    task_dstpath_drive.rstrip(':'),
                    task_dstpath_tail
                )
            )

            if os.path.realpath(record_dstpath_for_src) == record_dstpath_for_src:
                copy_success = copy_method_obj_symlink_record.copy(task_srcpath, record_dstpath_for_src)

            if os.path.realpath(record_dstpath_for_dst) == record_dstpath_for_dst:
                copy_success = copy_method_obj_symlink_record.copy(task_dstpath, record_dstpath_for_dst)



if __name__ == '__main__':
    main()
