
import copy
import collections
import fnmatch as fnmatch_module
import os
import re
import sys
import traceback

try:
    from tqdm import tqdm
    imported_tqdm = True
except ImportError:
    imported_tqdm = False

import psutils.custom_errors as cerr
import psutils.copymethod as psu_cm
import psutils.argtype as psu_at
from psutils.print_methods import *

from psutils.func import exhaust


##############################

### Argument globals ###

## Argument strings ("ARGSTR_")
ARGSTR_MINDEPTH = '--mindepth'
ARGSTR_MAXDEPTH = '--maxdepth'
ARGSTR_DMATCH_MAXDEPTH = '--dmatch-maxdepth'
ARGSTR_OUTDEPTH = '--outdepth'
ARGSTR_FMATCH = '--fmatch'
ARGSTR_FMATCH_RE = '--fmatch-re'
ARGSTR_FEXCL = '--fexcl'
ARGSTR_FEXCL_RE = '--fexcl-re'
ARGSTR_FSUB_RE = '--fsub-re'
ARGSTR_DMATCH = '--dmatch'
ARGSTR_DMATCH_RE = '--dmatch-re'
ARGSTR_DEXCL = '--dexcl'
ARGSTR_DEXCL_RE = '--dexcl-re'
ARGSTR_DSUB_RE = '--dsub-re'

## Argument groups ("ARGGRP_" lists of "ARGSTR_" argument strings)
ARGGRP_FILEMATCH = [
    ARGSTR_FMATCH, ARGSTR_FMATCH_RE, ARGSTR_FEXCL, ARGSTR_FEXCL_RE,
    ARGSTR_DMATCH, ARGSTR_DMATCH_RE, ARGSTR_DEXCL, ARGSTR_DEXCL_RE,
]

## Argument defaults ("ARGDEF_")
ARGDEF_MINDEPTH = 0
ARGDEF_MAXDEPTH = psu_at.ARGNUM_POS_INF
ARGDEF_DMATCH_MAXDEPTH = psu_at.ARGNUM_POS_INF
ARGDEF_OUTDEPTH = None

##############################

### Custom globals ###

WALK_LIST_FUNCTION_AVAIL = [os.listdir]
try:
    WALK_LIST_FUNCTION_DEFAULT = os.scandir
    WALK_LIST_FUNCTION_AVAIL.append(os.scandir)
except AttributeError:
    WALK_LIST_FUNCTION_DEFAULT = os.listdir
try:
    WALK_REMATCH_FUNCTION_DEFAULT = re.fullmatch
except AttributeError:
    WALK_REMATCH_FUNCTION_DEFAULT = re.match
WALK_REMATCH_PARTIAL_FUNCTION_DEFAULT = re.search
WALK_RESUB_FUNCTION_DEFAULT = re.sub

WALK_TRACK_FILES = 'files'
WALK_TRACK_DIRS = 'dirs'
WALK_TRACK_BOTH = 'both'
WALK_TRACK_ITEM_UNIT_DICT = {
    WALK_TRACK_FILES: 'file',
    WALK_TRACK_DIRS: 'folder',
    WALK_TRACK_BOTH: 'dirent'
}
WALK_TRACK_CHOICES = list(WALK_TRACK_ITEM_UNIT_DICT.keys())

FIND_RETURN_FILES = 'files'
FIND_RETURN_DIRS = 'dirs'
FIND_RETURN_MIX = 'mix'
FIND_RETURN_CHOICES = [
    FIND_RETURN_FILES,
    FIND_RETURN_DIRS,
    FIND_RETURN_MIX
]

##############################


def add_walk_arguments(parser,
                       mindepth=ARGDEF_MINDEPTH,
                       maxdepth=ARGDEF_MAXDEPTH,
                       dmatch_maxdepth=ARGDEF_DMATCH_MAXDEPTH,
                       outdepth=ARGDEF_OUTDEPTH):
    parser.add_argument(
        '-d0', ARGSTR_MINDEPTH,
        type=psu_at.ARGTYPE_NUM(argstr=ARGSTR_MINDEPTH,
            numeric_type=int, allow_neg=False, allow_zero=True, allow_inf=False),
        default=mindepth,
        help=' '.join([
            "Minimum depth of recursive search into source directories for files to copy.",
            "\nThe depth of a source directory's immediate contents is 1.",
        ])
    )
    parser.add_argument(
        '-d1', ARGSTR_MAXDEPTH,
        type=psu_at.ARGTYPE_NUM(argstr=ARGSTR_MAXDEPTH,
            numeric_type=int, allow_neg=False, allow_zero=True, allow_inf=True),
        default=maxdepth,
        help=' '.join([
            "Maximum depth of recursive search into source directories for files to copy.",
            "\nThe depth of a source directory's immediate contents is 1.",
        ])
    )
    parser.add_argument(
        ARGSTR_DMATCH_MAXDEPTH,
        type=psu_at.ARGTYPE_NUM(argstr=ARGSTR_DMATCH_MAXDEPTH,
            numeric_type=int, allow_neg=False, allow_zero=True, allow_inf=True),
        default=dmatch_maxdepth,
        help=' '.join([
            "[write me]",
        ])
    )
    parser.add_argument(
        ARGSTR_OUTDEPTH,
        type=psu_at.ARGTYPE_NUM(argstr=ARGSTR_OUTDEPTH,
            numeric_type=int, allow_neg=False, allow_zero=True, allow_inf=False),
        default=outdepth,
        help=' '.join([
            "[write me]",
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
        ARGSTR_FSUB_RE,
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
        ARGSTR_DSUB_RE,
        type=str,
        nargs=2,
        action='append',
        help=' '.join([
            "[write me]",
        ])
    )


def walk_simple(srcdir, mindepth=0, maxdepth=float('inf'), list_srcdname=False,
                list_function=WALK_LIST_FUNCTION_DEFAULT,
                track_item=None, track_initialize_total=True):

    if not os.path.isdir(srcdir):
        raise cerr.InvalidArgumentError("`srcdir` directory does not exist: {}".format(srcdir))
    if mindepth < 0 or maxdepth < 0:
        raise cerr.InvalidArgumentError("depth arguments must be >= 0")
    if track_item is not None:
        if not imported_tqdm:
            raise cerr.InvalidArgumentError("Python package 'tqdm' must be available to use `track_item` option")
        if track_item not in WALK_TRACK_CHOICES:
            raise cerr.InvalidArgumentError("`track_item` argument must be one of {}, "
                                            "but was {}".format(WALK_TRACK_CHOICES, track_item))
        track_item_unit = WALK_TRACK_ITEM_UNIT_DICT[track_item]
    else:
        track_item_unit = None
    if maxdepth == 0:
        track_initialize_total = False

    srcdir = os.path.abspath(srcdir)
    if track_item is not None:
        my_tftc = TrackFileTreeCount(track_item)
        my_tqdm = tqdm(total=0, unit=track_item_unit, disable=False)
        if track_initialize_total:
            print("First counting {}s to process in directory: {}".format(
                track_item_unit, srcdir
            ))
            my_tqdm.update(0)
            exhaust(
                _walk_simple(srcdir, 1, mindepth, maxdepth, list_function,
                             my_tftc, my_tqdm, update_total_count=True)
            )
            item_count, item_est = my_tftc.get_item_count_estimate()
            my_tqdm.close()
            print("Now processing {}s in directory: {}".format(
                track_item_unit, srcdir
            ))
            my_tqdm = tqdm(total=item_count, unit=track_item_unit, disable=False)
            my_tftc = TrackFileTreeCount(
                track_item,
                initial_file_estimate=my_tftc.total_file_estimate,
                initial_folder_estimate=my_tftc.total_folder_estimate,
                track_estimates=False
            )
        my_tqdm.update(0)
    else:
        my_tftc = None
        my_tqdm = None

    if list_srcdname and mindepth == 0:
        if my_tqdm is not None and track_item in (WALK_TRACK_DIRS, WALK_TRACK_BOTH):
            my_tqdm.total += 1
            my_tqdm.update(0)
        updir = os.path.dirname(srcdir)
        srcdname = os.path.basename(srcdir)
        yield updir, [srcdname], []
        if my_tqdm is not None and track_item in (WALK_TRACK_DIRS, WALK_TRACK_BOTH):
            my_tqdm.update(1)

    for x in _walk_simple(srcdir, 1, mindepth, maxdepth, list_function,
                          my_tftc, my_tqdm, (not track_initialize_total)):
        yield x

    if my_tqdm is not None:
        my_tqdm.close()


def _walk_simple(rootdir, depth, mindepth, maxdepth, list_function,
                 my_tftc=None, my_tqdm=None, update_total_count=False):
    if depth > maxdepth:
        return
    dnames, fnames = [], []
    for dirent in list_function(rootdir):
        if list_function is os.listdir:
            pname = dirent
            dirent_is_dir = os.path.isdir(os.path.join(rootdir, pname))
        else:
            pname = dirent.name
            dirent_is_dir = dirent.is_dir()
        (dnames if dirent_is_dir else fnames).append(pname)
    if mindepth <= depth:
        yield rootdir, dnames, fnames

    if my_tftc is not None and my_tqdm is not None:
        added_count = my_tftc.add(depth, len(dnames), len(fnames) if mindepth <= depth else 0)
        if update_total_count:
            if len(dnames) == 0:
                for i in range(depth+1, my_tftc.max_depth_found+1):
                    my_tftc.update_estimates(i)
            item_count, item_est = my_tftc.get_item_count_estimate()
            my_tqdm.total = int(item_est)
        my_tqdm.update(added_count)

    if depth < maxdepth:
        for dname in dnames:
            for x in _walk_simple(os.path.join(rootdir, dname), depth+1, mindepth, maxdepth, list_function,
                                  my_tftc, my_tqdm, update_total_count):
                yield x


class TrackFileTreeCount(object):

    def __init__(self, report_item=None,
                 initial_file_total=0,
                 initial_folder_total=0,
                 initial_file_estimate=0,
                 initial_folder_estimate=0,
                 track_estimates=True):
        if report_item is not None and report_item not in WALK_TRACK_CHOICES:
            raise cerr.InvalidArgumentError("`report_item` argument must be one of {}, "
                                            "but was {}".format(WALK_TRACK_CHOICES, report_item))
        self.report_item = report_item
        self.track_estimates = track_estimates

        self.total_folder_count = initial_folder_total
        self.total_file_count = initial_file_total
        self.total_folder_estimate = initial_folder_estimate
        self.total_file_estimate = initial_file_estimate

        if track_estimates:

            self.max_depth_found = 0

            self.nentries_at_depth = [1]
            self.nfolders_at_depth = [1]
            self.nfiles_at_depth = [0]

            # self.nfolders_per_entry_at_depth = [[1]]
            # self.nfiles_per_entry_at_depth = [[0]]
            self.nfolders_estimate_at_depth = [1]
            self.nfiles_estimate_at_depth = [0]

    def add(self, depth, nfolders, nfiles):

        self.total_folder_count += nfolders
        self.total_file_count += nfiles

        if self.track_estimates:

            added_depth = depth - self.max_depth_found
            if added_depth > 0:
                self.max_depth_found = depth

                self.nentries_at_depth.extend([0]*added_depth)
                self.nfolders_at_depth.extend([0]*added_depth)
                self.nfiles_at_depth.extend([0]*added_depth)

                # self.nfolders_per_entry_at_depth.extend([[]]*added_depth)
                # self.nfiles_per_entry_at_depth.extend([[]]*added_depth)
                self.nfolders_estimate_at_depth.extend([0]*added_depth)
                self.nfiles_estimate_at_depth.extend([0]*added_depth)

            self.nentries_at_depth[depth] += 1
            self.nfolders_at_depth[depth] += nfolders
            self.nfiles_at_depth[depth] += nfiles

            # self.nfolders_per_entry_at_depth[depth].append(nfolders)
            # self.nfiles_per_entry_at_depth[depth].append(nfiles)

            self.update_estimates(depth)

        return_added_count = None
        if self.report_item is not None:
            if self.report_item == WALK_TRACK_FILES:
                return_added_count = nfiles
            elif self.report_item == WALK_TRACK_DIRS:
                return_added_count = nfolders
            elif self.report_item == WALK_TRACK_BOTH:
                return_added_count = nfiles + nfolders

        return return_added_count

    def update_estimates(self, depth):
        # self.total_folder_estimate += self._update_estimate(depth, self.nfolders_at_depth, self.nfolders_per_entry_at_depth, self.nfolders_estimate_at_depth)
        # self.total_file_estimate += self._update_estimate(depth, self.nfiles_at_depth, self.nfiles_per_entry_at_depth, self.nfiles_estimate_at_depth)
        self.total_folder_estimate += self._update_estimate(depth, self.nfolders_at_depth, self.nfolders_estimate_at_depth)
        self.total_file_estimate += self._update_estimate(depth, self.nfiles_at_depth, self.nfiles_estimate_at_depth)

    # def _update_estimate(self, depth, nitems_at_depth, nitems_per_entry_at_depth, nitems_estimate_at_depth):
    def _update_estimate(self, depth, nitems_at_depth, nitems_estimate_at_depth):

        # total_entries_at_depth_thus_far = len(nitems_per_entry_at_depth[depth])
        total_entries_at_depth_thus_far = self.nentries_at_depth[depth]
        # total_items_at_depth_thus_far = sum(nitems_per_entry_at_depth[depth])
        total_items_at_depth_thus_far = nitems_at_depth[depth]

        estimated_total_entries_at_depth = self.nfolders_estimate_at_depth[depth-1]

        if estimated_total_entries_at_depth > total_entries_at_depth_thus_far:
            # average_item_count_per_entry = mean(nitems_per_entry_at_depth[depth])
            average_item_count_per_entry = total_items_at_depth_thus_far / total_entries_at_depth_thus_far
            estimated_additional_entries = estimated_total_entries_at_depth - total_entries_at_depth_thus_far
            estimated_additional_items = estimated_additional_entries * average_item_count_per_entry
        else:
            estimated_additional_items = 0

        old_estimate = nitems_estimate_at_depth[depth]
        new_estimate = total_items_at_depth_thus_far + estimated_additional_items

        nitems_estimate_at_depth[depth] = new_estimate

        return new_estimate - old_estimate

    def get_folder_count_estimate(self):
        return self.total_folder_count, self.total_folder_estimate

    def get_file_count_estimate(self):
        return self.total_file_count, self.total_file_estimate

    def get_item_count_estimate(self):
        if self.report_item == WALK_TRACK_FILES:
            return self.get_file_count_estimate()
        elif self.report_item == WALK_TRACK_DIRS:
            return self.get_folder_count_estimate()
        elif self.report_item == WALK_TRACK_BOTH:
            file_count, file_est = self.get_file_count_estimate()
            folder_count, folder_est = self.get_folder_count_estimate()
            return file_count + folder_count, file_est + folder_est
        else:
            return None, None


class WalkObject(object):
    def __init__(self,
        mindepth=None, maxdepth=float('inf'), outdepth=None, dmatch_maxdepth=None,
        fmatch=None, fmatch_re=None, fexcl=None, fexcl_re=None,
        dmatch=None, dmatch_re=None, dexcl=None, dexcl_re=None,
        fsub=None, dsub=None,
        copy_method=None, copy_overwrite_files=None, copy_overwrite_dirs=None, copy_overwrite_dmatch=None,
        sync_tree=False, transplant_tree=False, collapse_tree=False,
        copy_dryrun=None, copy_quiet=None, copy_debug=None,
        allow_dir_op=None,
        mkdir_upon_file_copy=False,
        allow_nonstd_shprogs=False,
        copy_shcmd_fmtstr=None,
        list_function=None,
        rematch_function=None,
        resub_function=None,
        rematch_partial=False
    ):
        if any([depth < 0 for depth in [mindepth, maxdepth, outdepth, dmatch_maxdepth] if depth is not None]):
            raise cerr.InvalidArgumentError("depth arguments must be >= 0")
        if outdepth is not None:
            if mindepth is not None and outdepth > mindepth:
                raise cerr.InvalidArgumentError("`outdepth` valid range: 0 <= `outdepth` <= `mindepth`")
            if sync_tree or transplant_tree:
                raise cerr.InvalidArgumentError("`outdepth` and (`sync_tree` or `transplant_tree`) "
                                                "arguments are incompatible")
        if copy_method and copy_shcmd_fmtstr:
            raise cerr.InvalidArgumentError("`copy_method` and `copy_shcmd_fmtstr` arguments are mutually exclusive")
        if copy_shcmd_fmtstr is not None:
            copy_method = copy_shcmd_fmtstr
            copy_method_is_fmtstr = True
        else:
            copy_method_is_fmtstr = False
        if copy_quiet and copy_dryrun:
            raise cerr.InvalidArgumentError("`copy_quiet` and `copy_dryrun` arguments are mutually exclusive")
        if list_function is not None and list_function not in WALK_LIST_FUNCTION_AVAIL:
            raise cerr.InvalidArgumentError("`list_function` must be either os.listdir or os.scandir")

        if mindepth is None:
            if outdepth is not None:
                mindepth = outdepth
            else:
                mindepth = 0

        if outdepth is None:
            if sync_tree or mindepth == 0:
                outdepth = 1
            elif transplant_tree:
                outdepth = 0
            else:
                outdepth = mindepth

        if dmatch_maxdepth is None:
            dmatch_maxdepth = float('inf') if copy_method is not None else -1

        list_function_given, rematch_function_given, resub_function_given = [
            item is not None for item in [
                list_function, rematch_function, resub_function
            ]
        ]
        if list_function is None:
            list_function = WALK_LIST_FUNCTION_DEFAULT
        if rematch_function is None:
            rematch_function = WALK_REMATCH_PARTIAL_FUNCTION_DEFAULT if rematch_partial else WALK_REMATCH_FUNCTION_DEFAULT
        if resub_function is None:
            resub_function = WALK_RESUB_FUNCTION_DEFAULT

        fmatch, fmatch_re, fexcl, fexcl_re, \
        dmatch, dmatch_re, dexcl, dexcl_re, \
        fsub, dsub = [
            item if (item is None or type(item) is list) else (list(item) if type(item) is tuple else [item]) for item in [
                fmatch, fmatch_re, fexcl, fexcl_re,
                dmatch, dmatch_re, dexcl, dexcl_re,
                fsub, dsub
            ]
        ]

        fsub, dsub = [
            item if (item is None or type(item[0]) in (list, tuple)) else [item] for item in [
                fsub, dsub
            ]
        ]

        fsub_patt = None
        dsub_patt = None
        try:
            if fsub is not None:
                fsub_patt, fsub_repl = list(zip(*fsub))
                fsub_patt = list(fsub_patt)
                if len(fsub_patt) != len(fsub_repl):
                    raise ValueError
            if dsub is not None:
                dsub_patt, dsub_repl = list(zip(*dsub))
                dsub_patt = list(dsub_patt)
                if len(dsub_patt) != len(dsub_repl):
                    raise ValueError
        except ValueError:
            raise cerr.InvalidArgumentError("resub arguments must be provided in (pattern, repl_str) groups")

        pattern_coll = [
            patt_list for patt_list in [
                fmatch, fmatch_re, fexcl, fexcl_re,
                dmatch, dmatch_re, dexcl, dexcl_re,
                fsub_patt, dsub_patt
            ] if patt_list is not None
        ]

        for patt_list in pattern_coll:
            for i, pattern in enumerate(patt_list):

                if patt_list in [fmatch, fexcl, dmatch, dexcl]:
                    pattern = fnmatch_module.translate(pattern)

                re_pattern = re.compile(pattern) if type(pattern) is str else pattern
                try:
                    re_pattern_str = re_pattern.pattern
                except AttributeError:
                    traceback.print_exc()
                    raise cerr.InvalidArgumentError("regex match/sub argument is invalid")
                if (    not rematch_function_given
                    and rematch_function is re.match and patt_list in [fmatch, dmatch]
                    and not pattern.endswith('$') and not rematch_partial):
                    if type(pattern) is str:
                        re_pattern = re.compile(pattern+'$')
                    else:
                        warning("`re.fullmatch` function is not supported, so `re.match` will be used instead "
                                "and argument regex match pattern '{}' may hit on a partial match")
                patt_list[i] = re_pattern

        fname_rematch = []
        for patt_list in [fmatch, fmatch_re]:
            if patt_list is not None:
                fname_rematch.extend(patt_list)
        fname_reexcl = []
        for patt_list in [fexcl, fexcl_re]:
            if patt_list is not None:
                fname_reexcl.extend(patt_list)
        dname_rematch = []
        for patt_list in [dmatch, dmatch_re]:
            if patt_list is not None:
                dname_rematch.extend(patt_list)
        dname_reexcl = []
        for patt_list in [dexcl, dexcl_re]:
            if patt_list is not None:
                dname_reexcl.extend(patt_list)
        fname_resub = list(zip(fsub_patt, fsub_repl)) if fsub is not None else None
        dname_resub = list(zip(dsub_patt, dsub_repl)) if dsub is not None else None

        if copy_method is not None:
            if type(copy_method) is psu_cm.CopyMethod:
                copy_method = copy.copy(copy_method)
            elif type(copy_method) is str:
                if copy_method in psu_cm.COPY_METHOD_DICT:
                    copy_method = psu_cm.COPY_METHOD_DICT[copy_method]
                else:
                    copy_method = psu_cm.CopyMethod(copy_method, copy_shcmd_is_fmtstr=copy_method_is_fmtstr)
                    if copy_method.copy_shprog not in psu_cm.COPY_METHOD_SHPROGS and not allow_nonstd_shprogs:
                        raise cerr.InvalidArgumentError("`copy_method` shell program '{}' is nonstandard and not allowed".format(copy_method.copy_shprog))
            else:
                copy_method = psu_cm.CopyMethod(copy_method)
            copy_method.set_options(
                check_srcpath_exists=False,
                copy_makedirs=False,
                copy_overwrite_files=copy_overwrite_files,
                copy_overwrite_dirs=copy_overwrite_dirs,
                copy_dryrun=copy_dryrun,
                copy_verbose=(None if copy_quiet is None else (not copy_quiet)),
                copy_debug=copy_debug
            )

        if allow_dir_op is None and copy_method.action_verb.upper() in ('SYMLINKING', 'MOVING'):
            allow_dir_op = True
        if copy_overwrite_dmatch is None:
            copy_overwrite_dmatch = False

        self.srcdir = None
        self.dstdir = None
        self.mindepth = mindepth
        self.maxdepth = maxdepth
        self.outdepth = outdepth
        self.outdepth_inst = outdepth
        self.dmatch_maxdepth = dmatch_maxdepth
        self.fname_rematch = fname_rematch
        self.fname_reexcl = fname_reexcl
        self.dname_rematch = dname_rematch
        self.dname_reexcl = dname_reexcl
        self.fname_resub = fname_resub
        self.dname_resub = dname_resub
        self.copy_method = copy_method
        self.copy_method_inst = None if copy_method is None else copy.copy(self.copy_method)
        self.collapse_tree = collapse_tree
        self.collapse_tree_inst = collapse_tree
        self.allow_dir_op = allow_dir_op
        self.mkdir_upon_file_copy = mkdir_upon_file_copy
        self.list_function = list_function
        self.rematch_function = rematch_function
        self.resub_function = resub_function
        self.tftc = None
        self.tqdm = None
        self.copy_overwrite_dmatch = copy_overwrite_dmatch

    def walk(self,
             srcdir, dstdir=None,
             copy_overwrite_files=None, copy_overwrite_dirs=None,
             sync_tree=False, transplant_tree=False, collapse_tree=None,
             copy_dryrun=None, copy_quiet=None, copy_debug=None):
        if collapse_tree is None:
            collapse_tree = self.collapse_tree

        if sync_tree:
            self.outdepth_inst = 1
        elif transplant_tree:
            self.outdepth_inst = 0
        else:
            self.outdepth_inst = self.outdepth

        srcdir = os.path.normpath(os.path.expanduser(srcdir))
        if not os.path.isdir(srcdir):
            raise cerr.InvalidArgumentError("`srcdir` directory does not exist: {}".format(srcdir))
        if dstdir is not None:
            dstdir = os.path.normpath(os.path.expanduser(dstdir))
        if self.outdepth_inst == 0:
            dstdir = os.path.join(dstdir, os.path.basename(srcdir))

        self.srcdir = srcdir
        self.dstdir = dstdir
        self.collapse_tree_inst = collapse_tree
        if self.copy_method is None:
            self.copy_method_inst = None
        else:
            self.copy_method_inst = copy.copy(self.copy_method)
            self.copy_method_inst.set_options(
                check_srcpath_exists=False,
                copy_makedirs=False,
                copy_overwrite_files=copy_overwrite_files,
                copy_overwrite_dirs=copy_overwrite_dirs,
                copy_dryrun=copy_dryrun,
                copy_verbose=(copy_quiet if copy_quiet is None else not copy_quiet),
                copy_debug=copy_debug
            )

        depth = 0
        dmatch_depth = -1 if not (self.dname_rematch or self.dname_reexcl) else 0

        if dmatch_depth == 0:
            srcdname = os.path.basename(self.srcdir)
            srcdname_match = True
            if self.dname_reexcl:
                for re_pattern in self.dname_reexcl:
                    srcdname_match = (not self.rematch_function(re_pattern, srcdname))
                    if not srcdname_match:
                        break
                if not srcdname_match:
                    return
            if self.dname_rematch and srcdname_match:
                srcdname_match = False
                for re_pattern in self.dname_rematch:
                    srcdname_match = self.rematch_function(re_pattern, srcdname)
                    if srcdname_match:
                        break
            if srcdname_match:
                dmatch_depth = 1

        if self.allow_dir_op and dmatch_depth != 0 and (self.mindepth <= depth <= self.maxdepth) and self.outdepth_inst in (-1, 0):
            if not self.copy_method_inst.dryrun:
                os.makedirs(os.path.dirname(os.path.abspath(self.dstdir)), exist_ok=True)
            copy_success = self.copy_method_inst.copy(
                self.srcdir, self.dstdir,
                overwrite_dir=(self.copy_method_inst.copy_overwrite_dirs or (self.copy_overwrite_dmatch and dmatch_depth == 1))
            )
            return

        if imported_tqdm:
            self.tftc = TrackFileTreeCount(WALK_TRACK_FILES)
            self.tqdm = tqdm(total=1, unit=WALK_TRACK_ITEM_UNIT_DICT[WALK_TRACK_FILES], disable=False)

        if self.copy_method_inst is not None and self.dstdir is not None and not os.path.isdir(self.dstdir):
            if not self.copy_method_inst.dryrun:
                os.makedirs(self.dstdir)

        depth = 1
        for x in self._walk(self.srcdir, self.dstdir, depth, dmatch_depth):
            yield x

        # if self.tqdm is not None:
        #     self.tqdm.close()
        #     self.tqdm = None

    def _walk(self, srcdir, dstdir, depth, dmatch_depth=-1):
        if depth > self.maxdepth and not (1 <= dmatch_depth <= self.dmatch_maxdepth):
            return

        # if depth == 1 and dmatch_depth == 0:
        #     srcdname = os.path.basename(srcdir)
        #     srcdname_match = True
        #     if self.dname_reexcl:
        #         for re_pattern in self.dname_reexcl:
        #             srcdname_match = (not self.rematch_function(re_pattern, srcdname))
        #             if not srcdname_match:
        #                 break
        #         if not srcdname_match:
        #             return
        #     if self.dname_rematch and srcdname_match:
        #         srcdname_match = False
        #         for re_pattern in self.dname_rematch:
        #             srcdname_match = self.rematch_function(re_pattern, srcdname)
        #             if srcdname_match:
        #                 break
        #     if srcdname_match:
        #         dmatch_depth = 1

        srcdir_passes = (dmatch_depth <= self.dmatch_maxdepth and dmatch_depth != 0)

        if dstdir is None or self.copy_method_inst is None:
            dstdir_exists = False
        elif os.path.isdir(dstdir):
            dstdir_exists = True
        elif self.mkdir_upon_file_copy:
            dstdir_exists = False
        elif srcdir_passes:
            if not self.copy_method_inst.dryrun:
                os.makedirs(dstdir)
            dstdir_exists = True
        else:
            dstdir_exists = False

        dnames_filtered, fnames_filtered = [], []
        dnames_filtered_pass = [] if self.dname_rematch else None

        for dirent in self.list_function(srcdir):
            if self.list_function is os.listdir:
                pname = dirent
                dirent_is_dir = os.path.isdir(os.path.join(srcdir, pname))
            else:
                pname = dirent.name
                dirent_is_dir = dirent.is_dir()

            if dirent_is_dir:
                dname_match = True
                if self.dname_reexcl:
                    for re_pattern in self.dname_reexcl:
                        dname_match = (not self.rematch_function(re_pattern, pname))
                        if not dname_match:
                            break
                    if not dname_match:
                        continue
                if dname_match:
                    dnames_filtered.append(pname)
                if self.dname_rematch:
                    dname_match = False
                    for re_pattern in self.dname_rematch:
                        dname_match = self.rematch_function(re_pattern, pname)
                        if dname_match:
                            break
                    if dname_match:
                        dnames_filtered_pass.append(True)
                    else:
                        dnames_filtered_pass.append(False)

            elif srcdir_passes:
                fname_match = True
                if self.fname_rematch:
                    fname_match = False
                    for re_pattern in self.fname_rematch:
                        fname_match = self.rematch_function(re_pattern, pname)
                        if fname_match:
                            break
                if self.fname_reexcl and fname_match:
                    for re_pattern in self.fname_reexcl:
                        fname_match = (not self.rematch_function(re_pattern, pname))
                        if not fname_match:
                            break
                if fname_match:
                    fnames_filtered.append(pname)

        if depth >= self.mindepth:

            if srcdir_passes and self.copy_method_inst is not None and dstdir is not None:
                if not dstdir_exists and (not self.mkdir_upon_file_copy or fnames_filtered):
                    if not self.copy_method_inst.dryrun:
                        os.makedirs(dstdir)
                    dstdir_exists = True
                for fname in fnames_filtered:
                    srcfile = os.path.join(srcdir, fname)
                    if self.fname_resub:
                        for re_pattern, repl_str in self.fname_resub:
                            fname = self.resub_function(re_pattern, repl_str, fname)
                    dstfile = os.path.join(dstdir, fname)
                    copy_success = self.copy_method_inst.copy(srcfile, dstfile)

            dnames_yield = (     dnames_filtered if (dnames_filtered_pass is None or srcdir_passes)
                            else [dn for i, dn in enumerate(dnames_filtered) if dnames_filtered_pass[i]])

            yield srcdir, dnames_yield, fnames_filtered

        if imported_tqdm:
            added_count = self.tftc.add(depth, len(dnames_filtered), len(fnames_filtered) if depth >= self.mindepth else 0)
            if len(dnames_filtered) == 0:
                for i in range(depth+1, self.tftc.max_depth_found+1):
                    self.tftc.update_estimates(i)
            item_count, item_est = self.tftc.get_item_count_estimate()
            self.tqdm.total = int(item_count)
            self.tqdm.update(added_count)

        if dnames_filtered and (depth < self.maxdepth or dmatch_depth != -1):
            depth_next = depth + 1

            if dmatch_depth == -1:
                pass
            elif depth <= self.maxdepth:
                dmatch_depth_next_pass = 1
                dmatch_depth_next_fail = 0 if dmatch_depth <= 0 else dmatch_depth + 1
            else:
                dmatch_depth_next_pass = dmatch_depth + 1
                dmatch_depth_next_fail = dmatch_depth_next_pass

            for i, dn in enumerate(dnames_filtered):
                srcdir_next_passes = (dnames_filtered_pass is None or dnames_filtered_pass[i])

                if depth == self.maxdepth and not (dmatch_depth > 0 or srcdir_next_passes):
                    continue

                srcdir_next = os.path.join(srcdir, dn)
                if dmatch_depth == -1:
                    dmatch_depth_next = -1
                else:
                    dmatch_depth_next = dmatch_depth_next_pass if srcdir_next_passes else dmatch_depth_next_fail

                if dstdir is None:
                    dstdir_next = None
                elif self.collapse_tree_inst:
                    # TODO: Make sure this is appropriate "collapse tree" behavior
                    dstdir_next = dstdir
                elif depth < self.outdepth_inst:
                    dstdir_next = dstdir
                else:
                    dstdname_next = dn
                    if self.dname_resub:
                        for re_pattern, repl_str in self.dname_resub:
                            dstdname_next = self.resub_function(re_pattern, repl_str, dstdname_next)
                    dstdir_next = os.path.join(dstdir, dstdname_next)

                if self.allow_dir_op and srcdir_next_passes and depth >= self.mindepth:
                    copy_success = self.copy_method_inst.copy(
                        srcdir_next, dstdir_next,
                        overwrite_dir=(self.copy_method.copy_overwrite_dirs or self.copy_overwrite_dmatch)
                    )
                else:
                    for x in self._walk(srcdir_next, dstdir_next, depth_next, dmatch_depth_next):
                        yield x


def _walk(
    srcdir, dstdir=None, list_srcdname=False,
    mindepth=None, maxdepth=float('inf'), outdepth=None, dmatch_maxdepth=None,
    fmatch=None, fmatch_re=None, fexcl=None, fexcl_re=None,
    dmatch=None, dmatch_re=None, dexcl=None, dexcl_re=None,
    fsub=None, dsub=None,
    copy_method=None, copy_overwrite_files=None, copy_overwrite_dirs=None, copy_overwrite_dmatch=None,
    sync_tree=False, transplant_tree=False, collapse_tree=False,
    copy_dryrun=None, copy_quiet=None, copy_debug=None,
    allow_dir_op=None,
    mkdir_upon_file_copy=False,
    allow_nonstd_shprogs=False,
    copy_shcmd_fmtstr=None,
    list_function=None,
    rematch_function=None,
    resub_function=None,
    rematch_partial=False
):
    if not os.path.isdir(srcdir):
        raise cerr.InvalidArgumentError("`srcdir` directory does not exist: {}".format(srcdir))
    # if dstdir is not None and copy_method is None:
    #     raise InvalidArgumentError("`copy_method` must be provided to utilize `dstdir` argument")
    if dstdir is None and (copy_method or copy_quiet or copy_dryrun or copy_shcmd_fmtstr):
        raise cerr.InvalidArgumentError("`dstdir` must be provided to use file copy options")
    walk_object = WalkObject(
        mindepth, maxdepth, outdepth, dmatch_maxdepth,
        fmatch, fmatch_re, fexcl, fexcl_re,
        dmatch, dmatch_re, dexcl, dexcl_re,
        fsub, dsub,
        copy_method, copy_overwrite_files, copy_overwrite_dirs, copy_overwrite_dmatch,
        sync_tree, transplant_tree, collapse_tree,
        copy_dryrun, copy_quiet, copy_debug,
        allow_dir_op,
        mkdir_upon_file_copy,
        allow_nonstd_shprogs,
        copy_shcmd_fmtstr,
        list_function,
        rematch_function,
        resub_function,
        rematch_partial
    )
    if list_srcdname and mindepth == 0:
        updir = os.path.dirname(srcdir)
        srcdname = os.path.basename(srcdir)
        yield updir, [srcdname], []
    for x in walk_object.walk(srcdir, dstdir):
        yield x


def walk(
    srcdir, dstdir=None, list_srcdname=False,
    mindepth=None, maxdepth=float('inf'), outdepth=None, dmatch_maxdepth=None,
    fmatch=None, fmatch_re=None, fexcl=None, fexcl_re=None,
    dmatch=None, dmatch_re=None, dexcl=None, dexcl_re=None,
    list_function=None,
    rematch_function=None,
    rematch_partial=False
):
    for x in _walk(
        srcdir, dstdir, list_srcdname,
        mindepth, maxdepth, outdepth, dmatch_maxdepth,
        fmatch, fmatch_re, fexcl, fexcl_re,
        dmatch, dmatch_re, dexcl, dexcl_re,
        list_function=list_function,
        rematch_function=rematch_function,
        rematch_partial=rematch_partial):
        yield x


def find(
    srcdir, dstdir=None, list_srcdname=False,
    vreturn=None, vyield=None, print_findings=False,
    mindepth=None, maxdepth=float('inf'), outdepth=None, dmatch_maxdepth=None,
    fmatch=None, fmatch_re=None, fexcl=None, fexcl_re=None,
    dmatch=None, dmatch_re=None, dexcl=None, dexcl_re=None,
    fsub=None, dsub=None,
    copy_method=None, copy_overwrite_files=None, copy_overwrite_dirs=None, copy_overwrite_dmatch=None,
    sync_tree=False, transplant_tree=False, collapse_tree=False,
    copy_dryrun=None, copy_quiet=None, copy_debug=None,
    allow_dir_op=None,
    mkdir_upon_file_copy=False,
    allow_nonstd_shprogs=False,
    copy_shcmd_fmtstr=None,
    list_function=None,
    rematch_function=None,
    resub_function=None,
    rematch_partial=False
):
    if vreturn is None and vyield is None:
        ffilter = ([arg is not None and len(arg) != 0 for arg in [fmatch, fmatch_re, fexcl, fexcl_re, fsub]].count(True) > 0)
        dfilter = ([arg is not None and len(arg) != 0 for arg in [dmatch, dmatch_re, dexcl, dexcl_re, dsub]].count(True) > 0)
        if ffilter and dfilter:
            vreturn = FIND_RETURN_MIX
        elif ffilter:
            vreturn = FIND_RETURN_FILES
        elif dfilter:
            vreturn = FIND_RETURN_DIRS
        else:
            vreturn = FIND_RETURN_MIX

    return_items = [item_list for item_list in [vreturn, vyield] if item_list is not None]
    if len(return_items) != 1:
        raise cerr.InvalidArgumentError("One and only one of (`vreturn`, `vyield`) arguments must be provided")
    if type(return_items[0]) in (tuple, list):
        return_items = list(return_items[0])
    for item in return_items:
        if item not in FIND_RETURN_CHOICES:
            raise cerr.InvalidArgumentError("`vreturn`/`vyield` string arguments must be one of {}, "
                                            "but argument was {}".format(FIND_RETURN_CHOICES, return_items))
    if 1 <= len(set(return_items)) <= 2:
        pass
    else:
        raise cerr.InvalidArgumentError("`vreturn`/`vyield` argument contains duplicate items")

    return_mix = (FIND_RETURN_MIX in return_items)
    return_mix_only = (return_items == [FIND_RETURN_MIX])

    dirs_all = []
    files_all = []
    mix_all = []
    def _find_iter():
        for rootdir, dnames, fnames in _walk(
            srcdir, dstdir, list_srcdname,
            mindepth, maxdepth, outdepth, dmatch_maxdepth,
            fmatch, fmatch_re, fexcl, fexcl_re,
            dmatch, dmatch_re, dexcl, dexcl_re,
            fsub, dsub,
            copy_method, copy_overwrite_files, copy_overwrite_dirs, copy_overwrite_dmatch,
            sync_tree, transplant_tree, collapse_tree,
            copy_dryrun, copy_quiet, copy_debug,
            allow_dir_op,
            mkdir_upon_file_copy,
            allow_nonstd_shprogs,
            copy_shcmd_fmtstr,
            list_function,
            rematch_function,
            resub_function,
            rematch_partial
        ):
            dirs = [os.path.join(rootdir, dn) for dn in dnames] if (FIND_RETURN_DIRS in return_items or return_mix) else None
            files = [os.path.join(rootdir, fn) for fn in fnames] if (FIND_RETURN_FILES in return_items or return_mix) else None
            if return_mix:
                mix = dirs if return_mix_only else list(dirs)
                mix.extend(files)
                if return_mix_only:
                    dirs, files = None, None
            else:
                mix = None

            if print_findings:
                if mix:
                    for p in mix:
                        sys.stdout.write(p+'\n')
                else:
                    if dirs:
                        for d in dirs:
                            sys.stdout.write(d+'\n')
                    if files:
                        for f in files:
                            sys.stdout.write(f+'\n')

            if vreturn:
                if dirs:
                    dirs_all.extend(dirs)
                if files:
                    files_all.extend(files)
                if mix:
                    mix_all.extend(mix)

            if vyield:
                if len(return_items) == 1:
                    item = return_items[0]
                    yield_results = files if item == FIND_RETURN_FILES else (dirs if item == FIND_RETURN_DIRS else mix)
                    for p in yield_results:
                        yield p
                else:
                    yield_results = []
                    for item in return_items:
                        yield_results.append(files if item == FIND_RETURN_FILES else (dirs if item == FIND_RETURN_DIRS else mix))
                    yield yield_results

    if vyield:
        return _find_iter()

    if vreturn:
        collections.deque(_find_iter(), maxlen=0)
        if len(return_items) == 1:
            item = return_items[0]
            return_results = files_all if item == FIND_RETURN_FILES else (dirs_all if item == FIND_RETURN_FILES else mix_all)
        else:
            return_results = []
            for item in return_items:
                return_results.append(files_all if item == FIND_RETURN_FILES else (dirs_all if item == FIND_RETURN_FILES else mix_all))
        return return_results


def copy_tree(
    srcdir, dstdir, copy_method='copy',
    sync_tree=False, transplant_tree=False, collapse_tree=False,
    overwrite_files=False, overwrite_dirs=False, overwrite_dmatch=False,
    mindepth=None, maxdepth=float('inf'), dmatch_maxdepth=None,
    fmatch=None, fmatch_re=None, fexcl=None, fexcl_re=None,
    dmatch=None, dmatch_re=None, dexcl=None, dexcl_re=None,
    fsub=None, dsub=None,
    vreturn=None, vyield=None, print_findings=False, list_srcdname=False,
    dryrun=False, quiet=False, debug=False,
    allow_dir_op=None,
    mkdir_upon_file_copy=False,
    allow_nonstd_shprogs=False,
    copy_shcmd_fmtstr=None,
    list_function=None,
    rematch_function=None,
    resub_function=None,
    rematch_partial=False
):
    if dstdir is None:
        raise cerr.InvalidArgumentError("`dstdir` cannot be None")
    if copy_method is None:
        raise cerr.InvalidArgumentError("`copy_method` cannot be None")
    find(
        srcdir, dstdir, list_srcdname,
        vreturn, vyield, print_findings,
        mindepth, maxdepth, dmatch_maxdepth,
        fmatch, fmatch_re, fexcl, fexcl_re,
        dmatch, dmatch_re, dexcl, dexcl_re,
        fsub, dsub,
        copy_method, overwrite_files, overwrite_dirs, overwrite_dmatch,
        sync_tree, transplant_tree, collapse_tree,
        dryrun, quiet, debug,
        allow_dir_op,
        mkdir_upon_file_copy,
        allow_nonstd_shprogs,
        copy_shcmd_fmtstr,
        list_function,
        rematch_function,
        resub_function,
        rematch_partial
    )
