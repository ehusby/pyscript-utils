
import collections
import os
import sys

import psutils.custom_errors as cerr

from psutils.walk import walk


FIND_RETURN_FILES = 1
FIND_RETURN_DIRS = 2
FIND_RETURN_MIX = 3
FIND_RETURN_ITEMS_DICT = {
    'files': FIND_RETURN_FILES,
    'dirs' : FIND_RETURN_DIRS,
    'mix'  : FIND_RETURN_MIX
}


def find(srcdir, dstdir=None,
        vreturn=None, vyield=None, debug=False,
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
    if vreturn is None and vyield is None:
        ffilter = ([arg is not None for arg in [fmatch, fmatch_re, fexcl, fexcl_re, fsub]].count(True) > 0)
        dfilter = ([arg is not None for arg in [dmatch, dmatch_re, dexcl, dexcl_re, dsub]].count(True) > 0)
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
    for i, item in enumerate(return_items):
        if type(item) is str:
            if item in FIND_RETURN_ITEMS_DICT:
                item = FIND_RETURN_ITEMS_DICT[item]
            else:
                raise cerr.InvalidArgumentError("`vreturn`/`vyield` string arguments must be one of {}, "
                                           "but was {}".format(list(FIND_RETURN_ITEMS_DICT.keys()), item))
        if type(item) is int and item not in list(FIND_RETURN_ITEMS_DICT.values()):
            raise cerr.InvalidArgumentError("`vreturn`/`vyield` int arguments must be one of {}, "
                                       "but was {}".format(list(FIND_RETURN_ITEMS_DICT.values()), item))
        return_items[i] = item
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
        for rootdir, dnames, fnames in walk(
            srcdir, dstdir, True,
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

            if debug:
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
                    yield_results = files if item == FIND_RETURN_FILES else (dirs if item == FIND_RETURN_FILES else mix)
                    for p in yield_results:
                        yield p
                else:
                    yield_results = []
                    for item in return_items:
                        yield_results.append(files if item == FIND_RETURN_FILES else (dirs if item == FIND_RETURN_FILES else mix))
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
