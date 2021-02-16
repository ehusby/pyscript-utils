#!/usr/bin/env python

# Erik Husby; Polar Geospatial Center, University of Minnesota; 2021


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
    # Check if PSU package is installed
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

import psutils.argtype as psu_at
import psutils.script_action as psu_act
import psutils.log as psu_log

import psutils.walk as psu_walk
import psutils.tasklist as psu_tl
import psutils.scheduler as psu_sched

##############################

### Script imports ###

## Python Standard Library

## Non-Standard PyPI
try:
    from tqdm import tqdm
    imported_tqdm = True
except ImportError:
    imported_tqdm = False

## Non-PyPI
import psutils.copymethod as psu_cm
from psutils.func import identity

##############################

### Argument globals ###

## Argument strings ("ARGSTR_")
# (positional first, then optional with '--' prefix)
ARGSTR_SRC_POS = 'src'
ARGSTR_DST_POS = 'dst'
ARGSTR_SRC = '--src'
ARGSTR_DST = '--dst'
ARGSTR_HARDLINK_RECORDS_DIR = '--hardlink-records-dir'
ARGSTR_NO_HARDLINK_RECORDS = '--no-hardlink-records'

## Argument help info ("ARGHLP_", only when needed outside of argparse)
# ARGHLP_SRCLIST_FORMAT = None  # set globally in pre_argparse()
# ARGHLP_SRCLIST_ROOTED_FORMAT = None  # set globally in pre_argparse()

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
ARGGRP_OUTDIR = [ARGSTR_HARDLINK_RECORDS_DIR]
ARGGRP_OUTDIR += psu_log.ARGGRP_OUTDIR  # comment-out if not using logging arguments
ARGGRP_OUTDIR += psu_sched.ARGGRP_OUTDIR  # comment-out if not using scheduler arguments

## Argument collections ("ARGCOL_" lists of "ARGGRP_" argument strings)
ARGCOL_MUT_EXCL_SET = [
    ARGGRP_DST,
    [psu_walk.ARGSTR_OUTDEPTH, [psu_tl.ARGSTR_SYNC_TREE, psu_tl.ARGSTR_TRANSPLANT_TREE]],
]
ARGCOL_MUT_EXCL_SET += psu_log.ARGCOL_MUT_EXCL_SET  # comment-out if not using logging arguments
ARGCOL_MUT_EXCL_SET += psu_tl.ARGCOL_MUT_EXCL_SET  # comment-out if not using source list arguments
ARGCOL_MUT_EXCL_SET += psu_act.ARGCOL_MUT_EXCL_SET  # comment-out if not using dryrun, debug, quiet arguments
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
# ARGCHO_COPY_METHOD_COPY = 'copy'
# ARGCHO_COPY_METHOD_MOVE = 'move'
# ARGCHO_COPY_METHOD_LINK = 'link'
# ARGCHO_COPY_METHOD_SYMLINK = 'symlink'
# ARGCHO_COPY_METHOD = [
#     ARGCHO_COPY_METHOD_COPY,
#     ARGCHO_COPY_METHOD_MOVE,
#     ARGCHO_COPY_METHOD_LINK,
#     ARGCHO_COPY_METHOD_SYMLINK
# ]
# # Argument choice object mapping ("ARGMAP_" dict of "ARGCHO_" argument options)
# ARGMAP_COPY_METHOD_FUNC = {
#     ARGCHO_COPY_METHOD_COPY: psu_cm.COPY_METHOD_COPY_DEFAULT,
#     ARGCHO_COPY_METHOD_MOVE: psu_cm.COPY_METHOD_MOVE,
#     ARGCHO_COPY_METHOD_LINK: psu_cm.COPY_METHOD_HARDLINK,
#     ARGCHO_COPY_METHOD_SYMLINK: psu_cm.COPY_METHOD_SYMLINK
# }

## Segregation of argument choices (lists of related argument choices)

## Argument settings
ARGSET_FLAGS = []
ARGSET_FLAGS += psu_log.ARGSET_FLAGS
ARGSET_CHOICES = []

## Argument defaults ("ARGDEF_")
ARGDEF_JOB_ABBREV = 'FileXfer'
ARGDEF_JOB_WALLTIME_HR = 1
ARGDEF_JOB_MEMORY_GB = 5
ARGDEF_COPY_METHOD = psu_cm.ARGCHO_COPY_METHOD_LINK
ARGDEF_MINDEPTH = 0
ARGDEF_MAXDEPTH = psu_at.ARGNUM_POS_INF
ARGDEF_DMATCH_MAXDEPTH = None
ARGDEF_OUTDEPTH = None
ARGDEF_SRCLIST_DELIM = ','
ARGDEF_BUNDLEDIR = os.path.realpath(os.path.join(os.path.expanduser('~'), 'scratch', 'task_bundles'))
ARGDEF_HARDLINK_RECORD_DIR = os.path.realpath(os.path.join(os.path.expanduser('~'), 'scratch', '{}_hardlink_records'.format(SCRIPT_NAME)))

##############################

### Logging argument defaults ###

ARGDEF_LOG_OUTFILE = None
ARGDEF_LOG_ERRFILE = None
ARGDEF_LOG_TASK_OUTEXT = None
ARGDEF_LOG_TASK_ERREXT = None
ARGDEF_LOG_OUTDIR = None
ARGDEF_LOG_LEVEL = psu_log.ARGCHO_LOG_LEVEL_INFO
ARGDEF_LOG_TASK_LEVEL = psu_log.ARGCHO_LOG_LEVEL_INFO
ARGDEF_LOG_MODE = psu_log.ARGCHO_LOG_MODE_APPEND

### Scheduler settings ###

BUNDLE_TASK_ARGSTRS = [ARGSTR_SRC, ARGSTR_DST]
BUNDLE_LIST_ARGSTR = psu_tl.ARGSTR_TASKLIST
BUNDLE_LIST_DESCR = 'tasklist'

##############################

### Custom globals ###


##############################

### Custom errors ###

# class MetaReadError(Exception):
#     def __init__(self, msg=""):
#         super(Exception, self).__init__(msg)

##############################


def pre_argparse():
    psu_tl.pre_argparse(ARGDEF_SRCLIST_DELIM, argstr_dst=ARGSTR_DST)


def argparser_init(skip_src_path_check=False, skip_dst_path_check=False,
                   src_prefix=None, src_suffix=None,
                   dst_prefix=None, dst_suffix=None):
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

    if not skip_src_path_check:
        argtype_src = psu_at.ARGTYPE_PATH(argstr=ARGSTR_SRC_POS,
            existcheck_fn=os.path.exists,
            existcheck_reqval=True,
            accesscheck_reqtrue=os.R_OK,
            append_prefix=src_prefix,
            append_suffix=src_suffix,)
    else:
        argtype_src = str
    parser.add_argument(
        ARGSTR_SRC_POS,
        type=argtype_src,
        nargs='+',
        action='append',
        help=' '.join([
            "Path to source file or directory to be copied.",
        ])
    )

    if not skip_dst_path_check:
        argtype_dst = psu_at.ARGTYPE_PATH(argstr=ARGSTR_DST_POS,
            accesscheck_reqtrue=os.W_OK,
            accesscheck_parent_if_dne=True,
            append_prefix=dst_prefix,
            append_suffix=dst_suffix,)
    else:
        argtype_dst = str
    parser.add_argument(
        ARGSTR_DST_POS,
        type=argtype_dst,
        help=' '.join([
            "Path to output file copy, or directory in which copies of source files will be created.",
            "To provide a destination directory that overrides all destination paths in source lists,",
            "use the {} argument instead of this argument.".format(psu_tl.ARGSTR_DSTDIR_GLOBAL)
        ])
    )


    ## Optional arguments

    parser.add_argument(
        '-s', ARGSTR_SRC,
        type=argtype_src,
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

    psu_tl.add_srclist_arguments(parser,
        ARGDEF_SRCLIST_DELIM
    )

    psu_cm.add_copymethod_arguments(parser,
        ARGDEF_COPY_METHOD
    )

    psu_walk.add_walk_arguments(parser,
        ARGDEF_MINDEPTH,
        ARGDEF_MAXDEPTH,
        ARGDEF_DMATCH_MAXDEPTH,
        ARGDEF_OUTDEPTH
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
            "If {}={}, this is the root directory in which a mirror of the current filesystem".format(psu_cm.ARGSTR_COPY_METHOD, psu_cm.ARGCHO_COPY_METHOD_LINK),
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

    psu_log.add_logging_arguments(parser,
        ARGDEF_LOG_OUTFILE,
        ARGDEF_LOG_ERRFILE,
        ARGDEF_LOG_TASK_OUTEXT,
        ARGDEF_LOG_TASK_ERREXT,
        ARGDEF_LOG_OUTDIR,
        ARGDEF_LOG_LEVEL,
        ARGDEF_LOG_TASK_LEVEL,
        ARGDEF_LOG_MODE
    )

    psu_act.add_action_arguments(parser)

    return parser


def main():

    ### Parse script arguments
    pre_argparse()
    arg_parser = argparser_init(skip_src_path_check=True, skip_dst_path_check=True)
    args = psu_act.parse_args(PYTHON_EXE, SCRIPT_FILE, arg_parser, sys.argv,
                              DOUBLED_ARGS, DOUBLED_ARGS_RESTRICTED_OPTGRP)
    # Parse again, incorporating any path modification arguments
    arg_parser = argparser_init(
        src_prefix=args.get(psu_tl.ARGSTR_SRCLIST_PREFIX),
        src_suffix=args.get(psu_tl.ARGSTR_SRCLIST_SUFFIX),
        dst_prefix=args.get(psu_tl.ARGSTR_SRCLIST_PREFIX_DST)
    )
    args = psu_act.parse_args(PYTHON_EXE, SCRIPT_FILE, arg_parser, sys.argv,
                              DOUBLED_ARGS, DOUBLED_ARGS_RESTRICTED_OPTGRP)

    ### Setup logging
    psu_log.setup_logging(capture_warnings=True)
    if args.get(psu_act.ARGSTR_DEBUG):
        psu_log.set_logger_level(psu_log.LEVEL_DEBUG)
    psu_act.setup_outfile_logging(args)
    task_log_level = psu_log.ARGMAP_LOG_LEVEL[args.get(psu_log.ARGSTR_LOG_TASK_LEVEL)]
    task_log_fh_mode = psu_log.ARGMAP_LOG_MODE_FH_MODE[args.get(psu_log.ARGSTR_LOG_MODE)]


    ### Adjust, Validate, and further Parse script argument values

    ## Apply usual argument adjustments
    psu_act.apply_argument_settings(args, ARGSET_FLAGS, ARGSET_CHOICES)
    psu_act.set_default_jobscript(args)  # for scheduler

    ## Restructure provided source arguments into flat lists
    psu_act.flatten_nargs_plus_action_append_lists(args, ARGGRP_SRC, psu_walk.ARGGRP_FILEMATCH)

    # If --outdepth is provided and --mindepth isn't provided, set mindepth to outdepth
    if args.provided(psu_walk.ARGSTR_OUTDEPTH) and not args.provided(psu_walk.ARGSTR_MINDEPTH):
        args.set(psu_walk.ARGSTR_MINDEPTH, args.get(psu_walk.ARGSTR_OUTDEPTH))

    ## Print script preamble when done adjusting argument values
    script_preamble = psu_act.get_preamble(args, sys.argv)
    if args.get(psu_act.ARGSTR_DEBUG):
        print(script_preamble)
    if args.get(psu_log.ARGSTR_LOG_OUTFILE) is not None:
        with open(args.get(psu_log.ARGSTR_LOG_OUTFILE), 'a') as fp_outlog:
            print(script_preamble, file=fp_outlog)

    ## Validate argument values
    psu_act.check_mutually_exclusive_args(args, ARGCOL_MUT_EXCL_SET, ARGCOL_MUT_EXCL_PROVIDED)

    # Verify mindepth and outdepth settings
    if (    args.get(psu_walk.ARGSTR_OUTDEPTH) is not None
        and args.get(psu_walk.ARGSTR_OUTDEPTH) > args.get(psu_walk.ARGSTR_MINDEPTH)):
        arg_parser.error("{} ({}) cannot be greater than {} ({})".format(
            psu_walk.ARGSTR_OUTDEPTH, args.get(psu_walk.ARGSTR_OUTDEPTH),
            psu_walk.ARGSTR_MINDEPTH, args.get(psu_walk.ARGSTR_MINDEPTH),
        ))

    ## Parse src-dst tasklist arguments
    skip_dstdir_path_adjustment = (    args.provided(psu_walk.ARGSTR_OUTDEPTH)
                                   or (args.provided(psu_walk.ARGSTR_MINDEPTH) and args.get(psu_walk.ARGSTR_MINDEPTH) > 0))
    all_task_list = psu_tl.parse_src_args(args, ARGSTR_SRC, ARGSTR_DST,
                                          skip_dir_adjust=skip_dstdir_path_adjustment)


    ### Create output directories if they don't already exist
    if not args.get(psu_act.ARGSTR_DRYRUN):
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
                dryrun=args.get(psu_act.ARGSTR_DRYRUN)
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

    copy_method_obj = copy.copy(psu_cm.ARGMAP_COPY_METHOD_FUNC[args.get(psu_cm.ARGSTR_COPY_METHOD)])
    copy_method_obj.set_options(
        copy_overwrite_files=args.get(psu_cm.ARGSTR_OVERWRITE_FILES),
        copy_overwrite_dirs=args.get(psu_cm.ARGSTR_OVERWRITE_DIRS),
        copy_dryrun=args.get(psu_act.ARGSTR_DRYRUN),
        copy_verbose=(not args.get(psu_act.ARGSTR_QUIET)),
        copy_debug=args.get(psu_act.ARGSTR_DEBUG)
    )

    walk_object = psu_walk.WalkObject(
        mindepth=args.get(psu_walk.ARGSTR_MINDEPTH), maxdepth=args.get(psu_walk.ARGSTR_MAXDEPTH),
        outdepth=args.get(psu_walk.ARGSTR_OUTDEPTH), dmatch_maxdepth=args.get(psu_walk.ARGSTR_DMATCH_MAXDEPTH),
        fmatch=args.get(psu_walk.ARGSTR_FMATCH), fmatch_re=args.get(psu_walk.ARGSTR_FMATCH_RE),
        fexcl=args.get(psu_walk.ARGSTR_FEXCL), fexcl_re=args.get(psu_walk.ARGSTR_FEXCL_RE),
        dmatch=args.get(psu_walk.ARGSTR_DMATCH), dmatch_re=args.get(psu_walk.ARGSTR_DMATCH_RE),
        dexcl=args.get(psu_walk.ARGSTR_DEXCL), dexcl_re=args.get(psu_walk.ARGSTR_DEXCL_RE),
        fsub=args.get(psu_walk.ARGSTR_FSUB_RE), dsub=args.get(psu_walk.ARGSTR_DSUB_RE),
        copy_method=copy_method_obj, copy_overwrite_files=args.get(psu_cm.ARGSTR_OVERWRITE_FILES), copy_overwrite_dirs=args.get(psu_cm.ARGSTR_OVERWRITE_DIRS), copy_overwrite_dmatch=args.get(psu_cm.ARGSTR_OVERWRITE_DMATCH),
        allow_dir_op=(False if args.get(psu_cm.ARGSTR_SYMLINK_FILES) else None), mkdir_upon_file_copy=args.get(psu_cm.ARGSTR_MKDIR_UPON_FILE_COPY),
        sync_tree=args.get(psu_tl.ARGSTR_SYNC_TREE), transplant_tree=args.get(psu_tl.ARGSTR_TRANSPLANT_TREE), collapse_tree=args.get(psu_tl.ARGSTR_COLLAPSE_TREE),
        copy_dryrun=args.get(psu_act.ARGSTR_DRYRUN), copy_quiet=args.get(psu_act.ARGSTR_QUIET), copy_debug=args.get(psu_act.ARGSTR_DEBUG),
    )

    do_record_hardlinks = (args.get(psu_cm.ARGSTR_COPY_METHOD) == psu_cm.ARGCHO_COPY_METHOD_LINK and not args.get(ARGSTR_NO_HARDLINK_RECORDS))
    if do_record_hardlinks:
        hardlink_record_dir = args.get(ARGSTR_HARDLINK_RECORDS_DIR)
        copy_method_obj_symlink_record = copy.copy(psu_cm.ARGMAP_COPY_METHOD_FUNC[psu_cm.ARGCHO_COPY_METHOD_SYMLINK])
        copy_method_obj_symlink_record.set_options(
            recursive_file_op=False,
            copy_overwrite_files=True,
            copy_overwrite_dirs=True,
            copy_dryrun=args.get(psu_act.ARGSTR_DRYRUN),
            copy_verbose=args.get(psu_act.ARGSTR_DEBUG),
            copy_debug=args.get(psu_act.ARGSTR_DEBUG)
        )

    tqdm_func = tqdm if imported_tqdm else identity
    for task_srcpath, task_dstpath in tqdm_func(task_list):
        if os.path.isfile(task_srcpath):
            task_srcfile = task_srcpath
            task_dstfile = task_dstpath
            copy_success = copy_method_obj.copy(task_srcfile, task_dstfile, srcpath_is_file=True)
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
