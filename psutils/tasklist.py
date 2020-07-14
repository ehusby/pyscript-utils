
import datetime
import math
import os
import traceback

import psutils.custom_errors as cerr

from psutils.string import get_index_fmtstr


def write_task_bundles(task_list, tasks_per_bundle,
                       dstdir, bundle_prefix,
                       task_delim=',', task_fmt='%s'):
    try:
        import numpy as np
        imported_numpy = True
    except ImportError:
        imported_numpy = False
        if task_fmt != '%s':
            raise
    bundle_prefix = os.path.join(dstdir, '{}_{}'.format(bundle_prefix, datetime.now().strftime("%Y%m%d%H%M%S")))
    jobnum_total = int(math.ceil(len(task_list) / float(tasks_per_bundle)))
    jobnum_fmt = get_index_fmtstr(jobnum_total)
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
        imported_numpy = True
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
        if ncol_min is not None and task_list_ncols < ncol_min:
            raise cerr.DimensionError("`bundle_file` line has {} columns, less than required minimum ({}): {}".format(
                                 task_list_ncols, ncol_min, bundle_file))
        if ncol_max is not None and task_list_ncols > ncol_max:
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

    if ncol_min is not None and task_list_ncols_min < ncol_min:
        raise cerr.DimensionError("`bundle_file` line has {} columns, less than required minimum ({}): {}".format(
                             task_list_ncols_min, ncol_min, bundle_file))
    if ncol_max is not None and task_list_ncols_max > ncol_max:
        raise cerr.DimensionError("`bundle_file` line has {} columns, more than required maximum ({}): {}".format(
                             task_list_ncols_max, ncol_max, bundle_file))

    if read_header and len(task_list) == 1 and type(task_list[0]) is list:
        task_list = task_list[0]

    return task_list


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
