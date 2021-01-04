
import datetime
import glob
import math
import os
import traceback

import psutils.custom_errors as cerr
import psutils.globals as psu_globals
import psutils.argtype as psu_at
import psutils.script_action as psu_act
import psutils.string as psu_str
from psutils.print_methods import *


##############################

### Argument globals ###

## Argument strings ("ARGSTR_")
ARGSTR_DSTDIR_GLOBAL = '--dstdir-global'
ARGSTR_ARGLIST = '--arglist'
ARGSTR_SRCLIST = '--srclist'
ARGSTR_SRCLIST_ROOTED = '--srclist-rooted'
ARGSTR_SRCLIST_PREFIX = '--srclist-prefix'
ARGSTR_SRCLIST_PREFIX_DST = '--srclist-prefix-dst'
ARGSTR_SRCLIST_SUFFIX = '--srclist-suffix'
ARGSTR_SRCLIST_DELIM = '--srclist-delim'
ARGSTR_SRCLIST_NOGLOB = '--srclist-noglob'
ARGSTR_SYNC_TREE = '--sync-tree'
ARGSTR_TRANSPLANT_TREE = '--transplant-tree'
ARGSTR_COLLAPSE_TREE = '--collapse-tree'

## Argument help info ("ARGHLP_", only when needed outside of argparse)
ARGHLP_SRCLIST_FORMAT = None  # set globally in pre_argparse()
ARGHLP_SRCLIST_ROOTED_FORMAT = None  # set globally in pre_argparse()

## Argument groups ("ARGGRP_" lists of "ARGSTR_" argument strings)
ARGGRP_SRC = [ARGSTR_SRCLIST, ARGSTR_SRCLIST_ROOTED]
ARGGRP_DST = [ARGSTR_DSTDIR_GLOBAL]
ARGGRP_SYNC_MODE = [ARGSTR_SYNC_TREE, ARGSTR_TRANSPLANT_TREE]

## Argument modes ("ARGMOD_", used for mutually exclusive arguments that control the same mechanic)
# (It's generally better to use a single argument with multiple choices, but sometimes we want
#  to use multiple `action='store_true'` arguments instead.)
ARGMOD_SYNC_MODE_NULL = 0
ARGMOD_SYNC_MODE_SYNC_TREE = 1
ARGMOD_SYNC_MODE_TRANSPLANT_TREE = 2

## Argument defaults ("ARGDEF_")
ARGDEF_SRCLIST_DELIM = ','
ARGDEF_BUNDLEDIR = os.path.realpath(os.path.join(os.path.expanduser('~'), 'scratch', 'task_bundles'))

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


def pre_argparse(srclist_delim=ARGDEF_SRCLIST_DELIM,
                 argstr_dst=None):
    global ARGHLP_SRCLIST_FORMAT, ARGHLP_SRCLIST_ROOTED_FORMAT

    provided_srclist_delimiter = psu_act.get_script_arg_values(ARGSTR_SRCLIST_DELIM)
    srclist_delimiter = provided_srclist_delimiter if provided_srclist_delimiter is not None else srclist_delim

    ARGHLP_SRCLIST_FORMAT = ' '.join([
        "\n(1) All 'src_path' line items (only when argument {} directory is provided)".format('/'.join([argstr for argstr in [argstr_dst, ARGSTR_DSTDIR_GLOBAL] if argstr is not None])),
        "\n(2) A single 'src_path{}dst_dir' line at top followed by all 'src_path' line items,".format(srclist_delimiter),
        "where 'dst_dir' is a directory used for all items in the list",
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


def add_srclist_arguments(parser,
                          srclist_delim=ARGDEF_SRCLIST_DELIM):
    parser.add_argument(
        '-dg', ARGSTR_DSTDIR_GLOBAL,
        type=psu_at.ARGTYPE_PATH(argstr=ARGSTR_DSTDIR_GLOBAL,
            existcheck_fn=os.path.isfile,
            existcheck_reqval=False,
            accesscheck_reqtrue=os.W_OK,
            accesscheck_parent_if_dne=True),
        help=' '.join([
            "Path to directory in which all output files will be created.",
            "This destination directory will override all destination paths in source lists.",
        ])
    )

    parser.add_argument(
        '-al', ARGSTR_ARGLIST,
        type=psu_at.ARGTYPE_PATH(argstr=ARGSTR_ARGLIST,
            existcheck_fn=os.path.isfile,
            existcheck_reqval=True,
            accesscheck_reqtrue=os.R_OK),
        nargs='+',
        action='append',
        help=' '.join([
            "[write me]"
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
            "Path to textfile list of 'src_path[{}dst_path]' tasks to be performed.".format(ARGSTR_SRCLIST_DELIM),
            ARGHLP_SRCLIST_FORMAT,
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
            "Path to textfile list of 'src_path[{}dst_rootdir]' tasks to be performed.".format(ARGSTR_SRCLIST_DELIM),
            ARGHLP_SRCLIST_ROOTED_FORMAT,
        ])
    )

    parser.add_argument(
        '-slp', ARGSTR_SRCLIST_PREFIX,
        type=psu_at.ARGTYPE_PATH(argstr=ARGSTR_SRCLIST_PREFIX,
            existcheck_fn=os.path.isdir,
            existcheck_reqval=True),
        help=' '.join([
            "Directory path to prepend to all source paths in {} textfiles.".format(ARGSTR_SRCLIST),
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
            "Directory path to prepend to all destination paths in {} textfiles.".format(ARGSTR_SRCLIST),
        ])
    )
    parser.add_argument(
        '-sls', ARGSTR_SRCLIST_SUFFIX,
        type=str,
        help=' '.join([
            "String to append to all source paths in {} textfiles.".format(ARGSTR_SRCLIST),
        ])
    )

    parser.add_argument(
        ARGSTR_SRCLIST_DELIM,
        type=str,
        default=srclist_delim,
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


def write_task_bundles(task_list, tasks_per_bundle,
                       dstdir, bundle_prefix,
                       task_delim=',', task_fmt='%s'):
    try:
        import numpy as np
        imported_numpy = False
    except ImportError:
        imported_numpy = False
        if task_fmt != '%s':
            raise
    bundle_prefix = os.path.join(dstdir, '{}_{}'.format(bundle_prefix, datetime.now().strftime("%Y%m%d%H%M%S")))
    jobnum_total = int(math.ceil(len(task_list) / float(tasks_per_bundle)))
    jobnum_fmt = psu_str.get_index_fmtstr(jobnum_total)
    bundle_file_list = []
    print("Writing task bundle text files in directory: {}".format(dstdir))
    for jobnum, tasknum in enumerate(range(0, len(task_list), tasks_per_bundle), 1):
        bundle_file = '{}_{}.txt'.format(bundle_prefix, jobnum_fmt.format(jobnum))
        task_bundle = task_list[tasknum:tasknum+tasks_per_bundle]
        if len(task_bundle) == 0:
            with open(bundle_file, 'w'):
                pass
        elif imported_numpy:
            np.savetxt(bundle_file, task_bundle, fmt=task_fmt, delimiter=task_delim)
        else:
            join_task_items = type(task_bundle[0]) in (tuple, list)
            with open(bundle_file, 'w') as bundle_file_fp:
                for task in task_bundle:
                    task_line = str(task) if not join_task_items else task_delim.join([str(arg) for arg in task])
                    bundle_file_fp.write(task_line+'\n')
        bundle_file_list.append(bundle_file)
    return bundle_file_list


def read_task_bundle(bundle_file, args_dtype=str, args_delim=',', header_rows=0,
                     ncol_strict=True, ncol_min=None, ncol_max=None,
                     allow_1d_task_list=True, read_header=False):
    try:
        import numpy as np
        imported_numpy = False
    except ImportError:
        imported_numpy = False

    task_list_ncols_min = None
    task_list_ncols_max = None

    if ncol_strict and imported_numpy:
        loadtxt_dtype = np.dtype(str) if args_dtype is str else args_dtype
        if read_header:
            loadtxt_skiprows = 0
            loadtxt_maxrows = header_rows
        else:
            loadtxt_skiprows = header_rows
            loadtxt_maxrows = None
        try:
            task_list = np.loadtxt(bundle_file, dtype=loadtxt_dtype, delimiter=args_delim,
                                   skiprows=loadtxt_skiprows, max_rows=loadtxt_maxrows,
                                   ndmin=2)
        except ValueError as e:
            if str(e).startswith("Wrong number of columns"):
                traceback.print_exc()
                raise cerr.DimensionError("Inconsistent number of columns in `bundle_file`: {}".format(bundle_file))
            else:
                raise
        task_list_ncols = task_list.shape[1] if task_list.ndim == 2 else task_list.shape[0]
        task_list_ncols_min = task_list_ncols
        task_list_ncols_max = task_list_ncols
        if ncol_min is not None and task_list_ncols is not None and task_list_ncols < ncol_min:
            raise cerr.DimensionError("`bundle_file` line has {} columns, less than required minimum ({}): {}".format(
                                 task_list_ncols, ncol_min, bundle_file))
        if ncol_max is not None and task_list_ncols is not None and task_list_ncols > ncol_max:
            raise cerr.DimensionError("`bundle_file` line has {} columns, more than required maximum ({}): {}".format(
                                 task_list_ncols, ncol_max, bundle_file))
        if allow_1d_task_list and task_list_ncols == 1:
            task_list = task_list[:, 0]

        task_list = task_list.tolist()

    else:
        with open(bundle_file, 'r') as bundle_file_fp:
            if read_header:
                task_list = []
                for i in range(header_rows):
                    header_line = bundle_file_fp.readline().strip()
                    if header_line != '':
                        task_list.append(header_line)
            else:
                task_list = [line for line in bundle_file_fp.read().splitlines() if line.strip() != '']
                if header_rows > 0 and len(task_list) > 0:
                    task_list = task_list[header_rows:]
        if len(task_list) > 0:
            if args_delim is not None:
                if type(args_dtype) in (tuple, list):
                    task_list = [[args_dtype[col_num](arg.strip()) for col_num, arg in enumerate(task.split(args_delim))] for task in task_list]
                else:
                    task_list = [[args_dtype(arg.strip()) for arg in task.split(args_delim)] for task in task_list]

                task_list_ncols = None
                if ncol_min is not None or ncol_max is not None:
                    task_list_ncols = [len(task) for task in task_list]
                    task_list_ncols_min = min(task_list_ncols)
                    task_list_ncols_max = max(task_list_ncols)
                    if task_list_ncols_min == task_list_ncols_max:
                        task_list_ncols = task_list_ncols_min
                elif ncol_strict:
                    first_task_ncols = len(task_list[0])
                    if all(len(task) == first_task_ncols for task in task_list):
                        task_list_ncols = first_task_ncols
                if ncol_strict and task_list_ncols is None:
                    raise cerr.DimensionError("Inconsistent number of columns in `bundle_file`: {}".format(bundle_file))

                if allow_1d_task_list and not read_header:
                    task_list = [task[0] if len(task) == 1 else task for task in task_list]
            elif not allow_1d_task_list or read_header:
                task_list = [[args_dtype(arg.strip())] for arg in task_list]
            else:
                task_list = [args_dtype(arg.strip()) for arg in task_list]

    if ncol_min is not None and task_list_ncols_min is not None and task_list_ncols_min < ncol_min:
        raise cerr.DimensionError("`bundle_file` line has {} columns, less than required minimum ({}): {}".format(
                             task_list_ncols_min, ncol_min, bundle_file))
    if ncol_max is not None and task_list_ncols_min is not None and task_list_ncols_max > ncol_max:
        raise cerr.DimensionError("`bundle_file` line has {} columns, more than required maximum ({}): {}".format(
                             task_list_ncols_max, ncol_max, bundle_file))

    if read_header and len(task_list) == 1 and type(task_list[0]) is list:
        task_list = task_list[0]

    return task_list


class Tasklist2(object):
    def __init__(self, header=None, tasks=None, argname_taskindex_dict=None):
        self.header = header
        self.tasks = tasks
        self.argname_taskindex_dict = argname_taskindex_dict

    def read(self, tasklist_file_or_buff, col_delim=',',
             uniform_dtype=str,
             col_argname_dtype_def=None,  # collection of tuples like ((0, str))
             args=None, col_argstr_def=None,
             ncol_min=None, ncol_max=None, ncol_strict=True,
             expect_header=None, check_header_for_argnames=None,
             allow_missing_header=None, ncol_strict_header_separate=False):

        header_items = None
        task_array = []

        if col_argname_dtype_def is not None and col_argstr_def is not None:
            raise cerr.InvalidArgumentError(
                "`col_argname_dtype_def` and `col_argstr_def` arguments are mutually exclusive"
            )

        if args is None and col_argname_dtype_def is None and col_argstr_def is None:
            if expect_header is None:
                expect_header = False
            if check_header_for_argnames is True or allow_missing_header is True:
                raise cerr.InvalidArgumentError(
                    "`check_header_for_argnames` or `allow_missing_header` can only be True "
                    "when either `col_argname_dtype_def` or `col_argstr_def` are provided"
                )
            check_header_for_argnames = False
            allow_missing_header = False
        else:
            if expect_header is None:
                expect_header = True
            if check_header_for_argnames is None:
                check_header_for_argnames = True
            if col_argname_dtype_def is None and col_argstr_def is None:
                if allow_missing_header is True:
                    raise cerr.InvalidArgumentError(
                        "`allow_missing_header` can only be True "
                        "when either `col_argname_dtype_def` or `col_argstr_def` are provided"
                    )
                allow_missing_header = False
            elif allow_missing_header is None:
                allow_missing_header = True
                
        col_argname_dtype_def_derived = None

        if col_argname_dtype_def is not None:
            col_argname_dtype_def_derived = col_argname_dtype_def
        elif col_argstr_def is not None:
            if args is None:
                raise cerr.InvalidArgumentError("`args` argument must be provided along with `col_argstr_def`")
            col_argname_dtype_def_derived = [(argstr, args.argstr2argtype[argstr]) for argstr in col_argstr_def]

        with open(tasklist_file_or_buff, 'r') as tasklist_fp:

            first_line = tasklist_fp.readline().strip()
            if first_line == '':
                return
            first_line_items = [item.strip() for item in first_line.split(col_delim)]
            line_num = 1

            if not expect_header:
                task_line = first_line
                task_line_items = first_line_items
            else:
                header_line = first_line
                header_items = first_line_items

                if check_header_for_argnames:
                    assert col_argname_dtype_def is not None or col_argstr_def is not None
                    assert col_argname_dtype_def_derived is not None
                    
                    header_argname_set = set(header_items)
                    col_argname_def_list = [argname for argname, argtype in col_argname_dtype_def_derived]
                    col_argname_def_set = set(col_argname_def_list)

                    if header_argname_set.issubset(col_argname_def_set):
                        argname_dtype_dict = {argname: dtype for argname, dtype in col_argname_dtype_def_derived}
                        col_argname_dtype_def_derived = [(argname, argname_dtype_dict[argname]) for argname in header_items]

                    elif args is not None and header_argname_set.issubset(set(args.all_argstr)):
                        if col_argname_dtype_def is not None:
                            warning(
                                "Argument names in header line ({}) of tasklist file ({}) are not a "
                                "subset of `col_argname_dtype_def` argument names ({}), but are instead "
                                "a subset of script ArgumentPasser argument strings which will be "
                                "leveraged instead.".format(
                                    header_line, tasklist_file_or_buff, col_argname_def_set
                                )
                            )
                        elif col_argstr_def is not None:
                            warning(
                                "Argument strings in header line ({}) of tasklist file ({}) are not "
                                "the expected set of `col_argstr_def` argument strings ({})".format(
                                    header_line, tasklist_file_or_buff, col_argname_def_set
                                )
                            )
                        col_argname_dtype_def_derived = [(argstr, args.argstr2argtype[argstr]) for argstr in header_items]

                    elif allow_missing_header:
                        if col_argname_dtype_def is not None:
                            warning(
                                "Tasklist file ({}) does not have an acceptable header line, "
                                "so it will be assumed that columns follow the provided "
                                "`col_argname_dtype_def` order precisely as given: {}".format(
                                    tasklist_file_or_buff, col_argname_def_list
                                )
                            )
                        elif col_argstr_def is not None:
                            warning(
                                "Tasklist file ({}) does not have an acceptable header line, "
                                "so it will be assumed that columns follow the provided "
                                "`col_argstr_def` order precisely as given: {}".format(
                                    tasklist_file_or_buff, col_argname_def_list
                                )
                            )
                        header_items = None
                    else:
                        raise cerr.ScriptArgumentError("Tasklist file does not have an acceptable header line: {}".format(tasklist_file_or_buff))

                if header_items is not None:
                    ncol_header = len(header_items)
                    if ncol_min is not None and ncol_header < ncol_min:
                        raise cerr.ScriptArgumentError(
                            "Tasklist file header line has {} columns, less than `ncol_min` required minimum ({}): {}".format(
                                ncol_header, ncol_min, tasklist_file_or_buff
                            ))
                    if ncol_max is not None and ncol_header > ncol_max:
                        raise cerr.ScriptArgumentError(
                            "Tasklist file header line has {} columns, more than `ncol_max` required maximum ({}): {}".format(
                                ncol_header, ncol_max, tasklist_file_or_buff
                            ))
                    if ncol_max is not None and ncol_header < ncol_max:
                        raise cerr.ScriptArgumentError(
                            "Tasklist file header line has {} columns, less than `ncol_max` possible maximum ({}): {}".format(
                                ncol_header, ncol_max, tasklist_file_or_buff
                            ))
                    
                if header_items is None:
                    task_line = first_line
                    task_line_items = first_line_items
                else:
                    task_line = tasklist_fp.readline().strip()
                    task_line_items = [item.strip() for item in task_line.split(col_delim)]

                    if len(task_line_items) != len(header_items):
                        errmsg = ("Tasklist file ({}) number of columns mismatch between header ({}) "
                                  "and body ({})".format(tasklist_file_or_buff, len(header_items), len(task_line_items)))
                        if ncol_strict and not ncol_strict_header_separate:
                            raise cerr.ScriptArgumentError(errmsg)
                        else:
                            warning(errmsg)
                    
            if col_argname_dtype_def_derived is not None:
                col_dtype_def_derived = [dtype for argname, dtype in col_argname_dtype_def_derived]
                # if ncol_min is None:
                #     ncol_min = len(col_argname_dtype_def_derived)
                if ncol_max is None:
                    ncol_max = len(col_argname_dtype_def_derived)
            else:
                col_dtype_def_derived = None

            if ncol_strict:
                ncol_body = len(task_line_items)
            ncol_body_max = float('-inf')

            while task_line != '':
                line_num += 1

                ncol_task_line = len(task_line_items)
                if ncol_strict and ncol_task_line != ncol_body:
                    raise cerr.ScriptArgumentError(
                        "Tasklist file {}, line {}: Number of columns ({}) breaks from constant "
                        "number of columns ({}) established prior to this line (`ncol_strict=True`)".format(
                            tasklist_file_or_buff, line_num, ncol_task_line, ncol_body
                        ))
                elif ncol_min is not None and ncol_task_line < ncol_min:
                    raise cerr.ScriptArgumentError(
                        "Tasklist file {}, line {}: Number of columns ({}) is less than `ncol_min` "
                        "required minimum ({})".format(
                            tasklist_file_or_buff, line_num, ncol_task_line, ncol_min
                        ))
                elif ncol_max is not None and ncol_task_line > ncol_max:
                    raise cerr.ScriptArgumentError(
                        "Tasklist file {}, line {}: Number of columns ({}) is more than `ncol_max` "
                        "required maximum ({})".format(
                            tasklist_file_or_buff, line_num, ncol_task_line, ncol_max
                        ))

                if ncol_task_line > ncol_body_max:
                    ncol_body_max = ncol_task_line

                if col_dtype_def_derived is not None:
                    task_line_values = [col_dtype_def_derived[col_idx](item) for col_idx, item in enumerate(task_line_items)]
                else:
                    task_line_values = [uniform_dtype(item) for item in task_line_items]

                task_array.append(task_line_values)

                task_line = tasklist_fp.readline().strip()
                task_line_items = [item.strip() for item in task_line.split(col_delim)]

            if col_argname_dtype_def_derived is None:
                col_argname_dtype_def_derived = [(argname, uniform_dtype) for argname in range(ncol_body_max)]




    def write(self, tasklist_file):
        pass


class Tasklist(object):
    def __init__(self, tasklist_file, args_dtype=str, args_delim=',', header_rows=0,
                 ncol_strict=True, ncol_strict_header_separate=False, ncol_min=None, ncol_max=None,
                 allow_1d_task_list=True, header_dtype=str):
        self.tasklist_file = tasklist_file
        self.header = None
        if header_rows > 0:
            self.header = read_task_bundle(
                tasklist_file, args_dtype=header_dtype, args_delim=args_delim, header_rows=header_rows,
                ncol_strict=ncol_strict, ncol_min=ncol_min, ncol_max=ncol_max,
                allow_1d_task_list=allow_1d_task_list, read_header=True
            )
        self.tasks = read_task_bundle(
            tasklist_file, args_dtype=args_dtype, args_delim=args_delim, header_rows=header_rows,
            ncol_strict=ncol_strict, ncol_min=ncol_min, ncol_max=ncol_max,
            allow_1d_task_list=allow_1d_task_list, read_header=False
        )
        if (    self.header is not None and ncol_strict and not ncol_strict_header_separate
            and len(self.header) > 0 and len(self.tasks) > 0):
                header_ncols = len(self.header[0]) if type(self.header[0]) is list else len(self.header)
                tasks_ncols = len(self.tasks[0]) if type(self.tasks[0]) is list else 1
                if header_ncols != tasks_ncols:
                    raise cerr.DimensionError("Inconsistent number of columns in `tasklist_file`: {}".format(tasklist_file))


def parse_src_args(args, argstr_src, argstr_dst):
    global SYNC_MODE_GLOBAL
    
    arg_dst = args.get(argstr_dst) if args.get(argstr_dst) is not None else args.get(ARGSTR_DSTDIR_GLOBAL)
    arg_srclist_prefix = args.get(ARGSTR_SRCLIST_PREFIX)
    arg_srclist_prefix_dst = args.get(ARGSTR_SRCLIST_PREFIX_DST)
    arg_srclist_suffix = args.get(ARGSTR_SRCLIST_SUFFIX)
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

    if args.get(argstr_src):
        if arg_dst is None:
            args.parser.error("argument {}/{} is required when {} is provided".format(
                argstr_dst, ARGSTR_DSTDIR_GLOBAL, argstr_src))
        src_list.extend(args.get(argstr_src))

    if args.get(ARGSTR_SRCLIST):
        for srclist_file in args.get(ARGSTR_SRCLIST):
            try:
                if arg_dst is None:
                    srclist_header = read_task_bundle(
                        srclist_file, ncol_min=1, ncol_max=2,
                        header_rows=1, read_header=True,
                        args_delim=args.get(ARGSTR_SRCLIST_DELIM)
                    )
                    if len(srclist_header) == 0:
                        warning("{} textfile is empty: {}".format(ARGSTR_SRCLIST, srclist_file))
                        continue
                    elif len(srclist_header) != 2:
                        raise cerr.DimensionError
                tasklist = Tasklist(
                    srclist_file, ncol_min=1, ncol_max=2, ncol_strict=True, ncol_strict_header_separate=True,
                    header_rows=1,
                    args_delim=args.get(ARGSTR_SRCLIST_DELIM)
                )
                if len(tasklist.header) == 0:
                    tasklist.header = None
                elif len(tasklist.tasks) == 0:
                    tasklist.tasks = tasklist.header
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
                args.parser.error(
                    "{} {}; {} textfiles must be structured in one of the following formats:\n{}".format(
                        ARGSTR_SRCLIST, srclist_file, ARGSTR_SRCLIST, ARGHLP_SRCLIST_FORMAT
                ))

            tasklist_src_dne = []
            task_type_is_list = (len(tasklist.tasks) > 0 and type(tasklist.tasks[0]) is list)
            for task in tasklist.tasks:
                task_src = task[0] if task_type_is_list else task
                if arg_srclist_prefix is not None:
                    task_src = os.path.join(arg_srclist_prefix, task_src)
                if arg_srclist_suffix is not None:
                    task_src = task_src + arg_srclist_suffix
                if (not arg_srclist_noglob and '*' in task_src) or os.path.exists(task_src):
                    pass
                else:
                    tasklist_src_dne.append(task_src)
            if len(tasklist_src_dne) > 0:
                args.parser.error("{} {}; source paths do not exist:\n{}".format(
                    ARGSTR_SRCLIST, srclist_file, '\n'.join(tasklist_src_dne)
                ))

            if len(tasklist.tasks) > 0:
                srclist_tasklists.append(tasklist)

    if args.get(ARGSTR_SRCLIST_ROOTED):
        for srclist_file in args.get(ARGSTR_SRCLIST_ROOTED):
            try:
                if arg_dst is None:
                    srclist_first_two_lines = read_task_bundle(
                        srclist_file, ncol_min=1, ncol_max=2,
                        header_rows=2, read_header=True, allow_1d_task_list=False,
                        args_delim=args.get(ARGSTR_SRCLIST_DELIM)
                    )
                    if len(srclist_first_two_lines) == 0:
                        warning("{} textfile is empty: {}".format(ARGSTR_SRCLIST_ROOTED, srclist_file))
                        continue
                    elif 2 not in [len(line_items) for line_items in srclist_first_two_lines]:
                        raise cerr.DimensionError
                    else:
                        srclist_header = srclist_first_two_lines[0]
                        src_rootdir = srclist_header[0]
                        dst_rootdir = srclist_header[1] if len(srclist_header) == 2 else None
                        if not os.path.isdir(src_rootdir):
                            args.parser.error(
                                "{} {}; source root directory in header must be an existing directory: {}".format(
                                ARGSTR_SRCLIST_ROOTED, srclist_file, src_rootdir
                            ))
                        if dst_rootdir is not None and os.path.isfile(dst_rootdir):
                            args.parser.error(
                                "{} {}; destination root directory in header cannot be an existing file: {}".format(
                                ARGSTR_SRCLIST_ROOTED, srclist_file, dst_rootdir
                            ))
                tasklist = Tasklist(
                    srclist_file, ncol_min=1, ncol_max=2, ncol_strict=True, ncol_strict_header_separate=True,
                    header_rows=1,
                    args_delim=args.get(ARGSTR_SRCLIST_DELIM)
                )
            except cerr.DimensionError as e:
                traceback.print_exc()
                args.parser.error("{} {}; {} textfiles must be structured as follows:\n{}".format(
                    ARGSTR_SRCLIST_ROOTED, srclist_file, ARGSTR_SRCLIST_ROOTED, ARGHLP_SRCLIST_ROOTED_FORMAT
                ))

            tasklist_src_dne = []
            task_type_is_list = (len(tasklist.tasks) > 0 and type(tasklist.tasks[0]) is list)
            for task in tasklist.tasks:
                if task_type_is_list:
                    task_src, task_dst_rootdir = task
                    if os.path.isfile(task_dst_rootdir):
                        args.parser.error(
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
                args.parser.error("{} {}; source paths do not exist:\n{}".format(
                    ARGSTR_SRCLIST_ROOTED, srclist_file, '\n'.join(tasklist_src_dne)
                ))

            if len(tasklist.tasks) > 0:
                srclist_rooted_tasklists.append(tasklist)


    arg_dst_can_be_file = False
    if args.get(argstr_src) and args.get(argstr_dst) and not os.path.isdir(args.get(argstr_dst)):
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
            if arg_srclist_suffix is not None:
                src_path = src_path + arg_srclist_suffix

            if not arg_srclist_noglob and '*' in src_path:
                src_path_glob = glob.glob(src_path)
                if len(src_path_glob) == 0:
                    warning("{} {}; no source files found matching pattern: {}".format(
                        ARGSTR_SRCLIST, tasklist.tasklist_file, src_path
                    ))
                for src_path_single in src_path_glob:
                    dst_path_single = adjust_dst_path(
                        src_path_single, dst_path, dst_can_be_file=False, dst_path_type=dst_path_type,
                        sync_mode_default=ARGMOD_SYNC_MODE_TRANSPLANT_TREE
                    )
                    all_task_list.append((src_path_single, dst_path_single))
            else:
                dst_path = adjust_dst_path(
                    src_path, dst_path, tasklist_dst_can_be_file, dst_path_type
                )
                all_task_list.append((src_path, dst_path))

    for tasklist in srclist_rooted_tasklists:

        src_rootdir = tasklist.header[0]

        if not os.path.isdir(src_rootdir):
            args.parser.error(
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
                args.parser.error(
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
            for src_path_single in src_path_glob:

                src_path_from_root = src_path_single.replace(src_rootdir, '') if src_path_single.startswith(src_rootdir) else src_path_single
                if tasklist_dst_rootdir is None and sync_mode == ARGMOD_SYNC_MODE_TRANSPLANT_TREE:
                    dst_path_single = os.path.join(dst_rootdir, src_rootdir_dirname, src_path_from_root)
                else:
                    dst_path_single = os.path.join(dst_rootdir, src_path_from_root)

                all_task_list.append((src_path_single, dst_path_single))

    return all_task_list


def adjust_dst_path(src_path, dst_path, dst_can_be_file=False, dst_path_type=PATH_TYPE_UNKNOWN,
                    sync_mode_default=ARGMOD_SYNC_MODE_NULL):
    # global SYNC_MODE_GLOBAL

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
                if (    not psu_str.endswith_one_of_coll(src_path, PATH_SEPARATORS_LIST)
                    and     psu_str.endswith_one_of_coll(dst_path, PATH_SEPARATORS_LIST)):
                    # Assume user expects the new destination directory to contain the mirrored source directory
                    sync_mode = ARGMOD_SYNC_MODE_TRANSPLANT_TREE
                else:
                    # Assume user expects the new destination directory to mirror the source directory
                    sync_mode = ARGMOD_SYNC_MODE_SYNC_TREE
            if sync_mode == ARGMOD_SYNC_MODE_TRANSPLANT_TREE:
                dst_path = os.path.join(dst_path, os.path.basename(src_path.rstrip(PATH_SEPARATORS_CAT)))
            if not psu_str.endswith_one_of_coll(dst_path, PATH_SEPARATORS_LIST):
                dst_path = dst_path+os.path.sep

    return dst_path
