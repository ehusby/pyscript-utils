
import copy
import fnmatch as fnmatch_module
import os
import re
import traceback

import psutils.custom_errors as cerr
from psutils.print_methods import *

import psutils.copymethod as psu_cm


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


def walk_simple(srcdir, mindepth=0, maxdepth=float('inf'), list_rootdname=False, list_function=WALK_LIST_FUNCTION_DEFAULT):
    if not os.path.isdir(srcdir):
        raise cerr.InvalidArgumentError("`srcdir` directory does not exist: {}".format(srcdir))
    if mindepth < 0 or maxdepth < 0:
        raise cerr.InvalidArgumentError("depth arguments must be >= 0")
    srcdir = os.path.abspath(srcdir)
    if list_rootdname and mindepth == 0:
        updir = os.path.dirname(srcdir)
        srcdname = os.path.basename(srcdir)
        yield updir, [srcdname], []
    for x in _walk(srcdir, 1, mindepth, maxdepth, list_function):
        yield x

def _walk(rootdir, depth, mindepth, maxdepth, list_function):
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
    if mindepth <= depth <= maxdepth:
        yield rootdir, dnames, fnames
    if depth < maxdepth:
        for dname in dnames:
            for x in _walk(os.path.join(rootdir, dname), depth+1, mindepth, maxdepth, list_function):
                yield x


class WalkObject(object):
    def __init__(self,
        mindepth=0, maxdepth=float('inf'), dmatch_maxdepth=None,
        fmatch=None, fmatch_re=None, fexcl=None, fexcl_re=None,
        dmatch=None, dmatch_re=None, dexcl=None, dexcl_re=None,
        fsub=None, dsub=None,
        copy_method=None, copy_overwrite=False, transplant_tree=False, collapse_tree=False,
        copy_dryrun=False, copy_quiet=False, copy_debug=False,
        mkdir_upon_file_copy=False,
        allow_nonstd_shprogs=False,
        copy_shcmd_fmtstr=None,
        list_function=None,
        rematch_function=None,
        resub_function=None,
        rematch_partial=False):

        if mindepth < 0 or maxdepth < 0 or (dmatch_maxdepth is not None and dmatch_maxdepth < 0):
            raise cerr.InvalidArgumentError("depth arguments must be >= 0")
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

        if dmatch is None and dmatch_re is None:
            dmatch_nomaxdepth = True
        else:
            if copy_method is None:
                dmatch_nomaxdepth = (dmatch_maxdepth is None)
            else:
                dmatch_nomaxdepth = False
        if dmatch_maxdepth is None:
            dmatch_maxdepth = float('inf')

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
            item if (item is None or type(item) is list) else (list(item) if type(item) in tuple else [item]) for item in [
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
            copy_method.set_options(copy_overwrite=copy_overwrite, dryrun=copy_dryrun, verbose=(not copy_quiet), debug=copy_debug)

        self.srcdir = None
        self.dstdir = None
        self.mindepth = mindepth
        self.maxdepth = maxdepth
        self.dmatch_maxdepth = dmatch_maxdepth
        self.dmatch_nomaxdepth = dmatch_nomaxdepth
        self.fname_rematch = fname_rematch
        self.fname_reexcl = fname_reexcl
        self.dname_rematch = dname_rematch
        self.dname_reexcl = dname_reexcl
        self.fname_resub = fname_resub
        self.dname_resub = dname_resub
        self.copy_method = copy_method
        self.copy_method_inst = copy_method
        self.transplant_tree = transplant_tree
        self.collapse_tree = collapse_tree
        self.collapse_tree_inst = collapse_tree
        self.mkdir_upon_file_copy = mkdir_upon_file_copy
        self.list_function = list_function
        self.rematch_function = rematch_function
        self.resub_function = resub_function

    def walk(self,
             srcdir, dstdir=None,
             copy_overwrite=None, transplant_tree=None, collapse_tree=None):
        if copy_overwrite is None:
            copy_overwrite = self.copy_method.copy_overwrite
        if transplant_tree is None:
            transplant_tree = self.transplant_tree
        if collapse_tree is None:
            collapse_tree = self.collapse_tree

        srcdir = os.path.normpath(os.path.expanduser(srcdir))
        if not os.path.isdir(srcdir):
            raise cerr.InvalidArgumentError("`srcdir` directory does not exist: {}".format(srcdir))
        if dstdir is not None:
            dstdir = os.path.normpath(os.path.expanduser(dstdir))
        if transplant_tree:
            dstdir = os.path.join(dstdir, os.path.basename(srcdir))

        self.srcdir = srcdir
        self.dstdir = dstdir
        if copy_overwrite != self.copy_method.copy_overwrite:
            self.copy_method_inst = copy.copy(self.copy_method)
            self.copy_method_inst.set_options(copy_overwrite=copy_overwrite)
        else:
            self.copy_method_inst = self.copy_method
        self.collapse_tree_inst = collapse_tree

        if self.copy_method is not None and self.dstdir is not None and not os.path.isdir(self.dstdir):
            if not self.copy_method_inst.dryrun:
                os.makedirs(self.dstdir)

        depth = 1
        dmatch_depth = -1 if self.dmatch_nomaxdepth else 0

        for x in self._walk(self.srcdir, self.dstdir, depth, dmatch_depth):
            yield x

    def _walk(self, srcdir, dstdir, depth, dmatch_depth):
        if depth > self.maxdepth:
            return
        if depth == 1 and dmatch_depth == 0:
            srcdname = os.path.basename(srcdir)
            srcdname_match = True
            if self.dname_rematch:
                srcdname_match = False
                for re_pattern in self.dname_rematch:
                    srcdname_match = self.rematch_function(re_pattern, srcdname)
                    if srcdname_match:
                        break
            if self.dname_reexcl and srcdname_match:
                for re_pattern in self.dname_reexcl:
                    srcdname_match = (not self.rematch_function(re_pattern, srcdname))
                    if not srcdname_match:
                        break
            if srcdname_match:
                dmatch_depth = 1

        srcdname_passes = (dmatch_depth <= self.dmatch_maxdepth and dmatch_depth != 0)

        if dstdir is None or self.copy_method_inst is None:
            dstdir_exists = False
        elif os.path.isdir(dstdir):
            dstdir_exists = True
        elif self.mkdir_upon_file_copy:
            dstdir_exists = False
        elif srcdname_passes:
            if not self.copy_method_inst.dryrun:
                os.makedirs(dstdir)
            dstdir_exists = True
        else:
            dstdir_exists = False

        dnames, fnames_filtered = [], []
        dnames_pass = [] if (self.dname_rematch or self.dname_reexcl) else None
        for dirent in self.list_function(srcdir):
            if self.list_function is os.listdir:
                pname = dirent
                dirent_is_dir = os.path.isdir(os.path.join(srcdir, pname))
            else:
                pname = dirent.name
                dirent_is_dir = dirent.is_dir()
            if dirent_is_dir:
                dnames.append(pname)
                if dnames_pass is not None:
                    dname_match = True
                    if self.dname_rematch:
                        dname_match = False
                        for re_pattern in self.dname_rematch:
                            dname_match = self.rematch_function(re_pattern, pname)
                            if dname_match:
                                break
                    if self.dname_reexcl and dname_match:
                        for re_pattern in self.dname_reexcl:
                            dname_match = (not self.rematch_function(re_pattern, pname))
                            if not dname_match:
                                break
                    if dname_match:
                        dnames_pass.append(True)
                    else:
                        dnames_pass.append(False)
            elif srcdname_passes:
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
            if srcdname_passes and self.copy_method_inst is not None and dstdir is not None:
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
                    self.copy_method_inst.copy(srcfile, dstfile)
            if srcdname_passes and not self.dmatch_nomaxdepth:
                dnames_filtered = dnames
            else:
                dnames_filtered = dnames if dnames_pass is None else [dn for i, dn in enumerate(dnames) if dnames_pass[i]]
            yield srcdir, dnames_filtered, fnames_filtered

        if dnames and depth < self.maxdepth:
            depth_next = depth + 1
            dmatch_depth_next_pass = dmatch_depth if dmatch_depth <  0 else 1
            dmatch_depth_next_fail = dmatch_depth if dmatch_depth <= 0 else dmatch_depth + 1
            for i, dn in enumerate(dnames):
                srcdir_next = os.path.join(srcdir, dn)
                dmatch_depth_next = dmatch_depth_next_pass if dnames_pass is None or dnames_pass[i] else dmatch_depth_next_fail
                if dstdir is None:
                    dstdir_next = None
                elif self.collapse_tree_inst:
                    dstdir_next = dstdir
                else:
                    dstdname_next = dn
                    if self.dname_resub:
                        for re_pattern, repl_str in self.dname_resub:
                            dstdname_next = self.resub_function(re_pattern, repl_str, dstdname_next)
                    dstdir_next = os.path.join(dstdir, dstdname_next)
                for x in self._walk(srcdir_next, dstdir_next, depth_next, dmatch_depth_next):
                    yield x


def walk(srcdir, dstdir=None, list_rootdname=False,
        mindepth=0, maxdepth=float('inf'), dmatch_maxdepth=None,
        fmatch=None, fmatch_re=None, fexcl=None, fexcl_re=None,
        dmatch=None, dmatch_re=None, dexcl=None, dexcl_re=None,
        fsub=None, dsub=None,
        copy_method=None, copy_overwrite=False, transplant_tree=False, collapse_tree=False,
        copy_dryrun=False, copy_quiet=False, copy_debug=False,
        mkdir_upon_file_copy=False,
        allow_nonstd_shprogs=False,
        copy_shcmd_fmtstr=None,
        list_function=None,
        rematch_function=None,
        resub_function=None,
        rematch_partial=False):
    if not os.path.isdir(srcdir):
        raise cerr.InvalidArgumentError("`srcdir` directory does not exist: {}".format(srcdir))
    # if dstdir is not None and copy_method is None:
    #     raise InvalidArgumentError("`copy_method` must be provided to utilize `dstdir` argument")
    if dstdir is None and (copy_method or copy_quiet or copy_dryrun or copy_shcmd_fmtstr):
        raise cerr.InvalidArgumentError("`dstdir` must be provided to use file copy options")
    walk_object = WalkObject(
        mindepth, maxdepth, dmatch_maxdepth,
        fmatch, fmatch_re, fexcl, fexcl_re,
        dmatch, dmatch_re, dexcl, dexcl_re,
        fsub, dsub,
        copy_method, copy_overwrite, transplant_tree, collapse_tree,
        copy_dryrun, copy_quiet, copy_debug,
        mkdir_upon_file_copy,
        allow_nonstd_shprogs,
        copy_shcmd_fmtstr,
        list_function,
        rematch_function,
        resub_function,
        rematch_partial
    )
    if list_rootdname and mindepth == 0:
        updir = os.path.dirname(srcdir)
        srcdname = os.path.basename(srcdir)
        yield updir, [srcdname], []
    for x in walk_object.walk(srcdir, dstdir, copy_overwrite, transplant_tree, collapse_tree):
        yield x
