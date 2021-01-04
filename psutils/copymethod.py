
import filecmp
import os
import shutil
import stat
import types

import psutils.globals as psu_globals
from psutils.print_methods import *

from psutils.shell import execute_shell_command


COPY_METHOD_VERB_TO_GERUND_DICT = {
    'link': 'linking',
    'move': 'moving',
    'copy': 'copying'
}
COPY_METHOD_SHPROGS_LINUX_TO_WINDOWS_DICT = {
    'ln': 'mklink',
    'cp': 'copy',
    'mv': 'move'
}
COPY_METHOD_SHPROGS_ACTION_VERB_DICT = dict()
for prog in ['ln', 'mklink']:
    COPY_METHOD_SHPROGS_ACTION_VERB_DICT[prog] = 'linking'
for prog in ['cp', 'copy']:
    COPY_METHOD_SHPROGS_ACTION_VERB_DICT[prog] = 'copying'
for prog in ['mv', 'move']:
    COPY_METHOD_SHPROGS_ACTION_VERB_DICT[prog] = 'moving'


class CopyMethod(object):
    def __init__(self,
                 copy_fn, copy_fn_name=None, action_verb=None,
                 reverse_args=None, copy_shcmd_is_fmtstr=False):
        copy_shcmd = None
        copy_shprog = None
        copy_fn_type = type(copy_fn)

        if copy_fn_name is None and copy_fn_type is not str:
            if copy_fn_type in [types.FunctionType, types.BuiltinFunctionType, types.BuiltinMethodType]:
                try:
                    copy_fn_name = copy_fn_type.__name__
                except AttributeError:
                    pass
            if copy_fn_name is None:
                copy_fn_name = str(copy_fn)

        if copy_fn_type is str:
            copy_shcmd = copy_fn.strip()
            copy_shcmd_parts = copy_shcmd.split(' ')
            copy_shprog = copy_shcmd_parts[0]
            if psu_globals.SYSTYPE == psu_globals.SYSTYPE_WINDOWS and copy_shprog in COPY_METHOD_SHPROGS_LINUX_TO_WINDOWS_DICT and len(copy_shcmd_parts) == 1:
                copy_shprog = COPY_METHOD_SHPROGS_LINUX_TO_WINDOWS_DICT[copy_shprog]
                copy_shcmd_parts[0] = copy_shprog
                copy_shcmd = ' '.join(copy_shcmd_parts)
            if copy_shprog == 'mklink' and reverse_args is None:
                reverse_args = True
            if action_verb is None and copy_shprog in COPY_METHOD_SHPROGS_ACTION_VERB_DICT:
                action_verb = COPY_METHOD_SHPROGS_ACTION_VERB_DICT[copy_shprog]

        if action_verb is None:
            if copy_shprog is None:
                copy_shprog_verbose = None
            elif copy_shprog in COPY_METHOD_SHPROGS_LINUX_TO_WINDOWS_DICT:
                copy_shprog_verbose = COPY_METHOD_SHPROGS_LINUX_TO_WINDOWS_DICT[copy_shprog]
            else:
                copy_shprog_verbose = copy_shprog
            if copy_shprog_verbose is not None or copy_fn_name is not None:
                for verb in COPY_METHOD_VERB_TO_GERUND_DICT:
                    if (   (copy_shprog_verbose is not None and verb in copy_shprog_verbose)
                        or (copy_fn_name is not None and verb in copy_fn_name)):
                        action_verb = COPY_METHOD_VERB_TO_GERUND_DICT[verb]
                        break
            if action_verb is None:
                action_verb = 'transferring'
        action_verb = action_verb.upper()

        if reverse_args is None:
            reverse_args = False

        self.copy_fn = copy_fn
        self.copy_fn_name = copy_fn_name
        self.action_verb = action_verb
        self.reverse_args = reverse_args
        self.copy_shcmd = copy_shcmd
        self.copy_shprog = copy_shprog
        self.copy_shcmd_is_fmtstr = copy_shcmd_is_fmtstr

        self.check_srcpath_exists = True
        self.copy_makedirs = True
        self.copy_overwrite_files = False
        self.copy_overwrite_dirs = False
        self.dryrun = False
        self.verbose = True
        self.debug = False

    def __copy__(self):
        copy_method = CopyMethod(self.copy_fn, self.copy_fn_name, self.action_verb,
                                 self.reverse_args, self.copy_shcmd_is_fmtstr)
        copy_method.set_options(self.check_srcpath_exists, self.copy_makedirs, self.copy_overwrite_files, self.copy_overwrite_dirs, self.dryrun, self.verbose, self.debug)
        return copy_method

    def set_options(self, check_srcpath_exists=None, copy_makedirs=None, copy_overwrite_files=None, copy_overwrite_dirs=None, copy_dryrun=None, copy_verbose=None, copy_debug=None):
        if check_srcpath_exists:
            self.check_srcpath_exists = check_srcpath_exists
        if copy_makedirs is not None:
            self.copy_makedirs = copy_makedirs
        if copy_overwrite_files is not None:
            self.copy_overwrite_files = copy_overwrite_files
        if copy_overwrite_dirs is not None:
            self.copy_overwrite_dirs = copy_overwrite_dirs
        if copy_dryrun is not None:
            self.dryrun = copy_dryrun
        if copy_verbose is not None:
            self.verbose = copy_verbose
        if copy_debug is not None:
            self.debug = copy_debug

    def copy(self, srcpath, dstpath,
             overwrite_file=None, overwrite_dir=None):

        if overwrite_file is None:
            overwrite_file = self.copy_overwrite_files
        if overwrite_dir is None:
            overwrite_dir = self.copy_overwrite_dirs

        copy_info = None
        proceed_with_copy = False

        srcpath_stat = None
        dstpath_stat = None

        if self.check_srcpath_exists and os.path.exists(srcpath):
            srcpath_stat = os.stat(srcpath)

        if self.check_srcpath_exists and srcpath_stat is None:
            copy_info = "SKIPPING; source path does not exist"
            proceed_with_copy = False
        else:
            if not os.path.exists(dstpath):
                proceed_with_copy = True
            else:
                dstpath_stat = os.stat(dstpath)
                if stat.S_ISDIR(dstpath_stat.st_mode):
                    # dstpath is a directory
                    if overwrite_dir:
                        copy_info = "OVERWRITING DIRECTORY"
                        proceed_with_copy = True
                    else:
                        copy_info = "SKIPPING; destination directory already exists"
                        proceed_with_copy = False
                else:
                    # dstpath is a file
                    if overwrite_file:
                        copy_info = "OVERWRITING FILE"
                        proceed_with_copy = True
                    elif self.action_verb in ['HARDLINKING', 'LINKING']:
                        if srcpath_stat is None:
                            srcpath_stat = os.stat(srcpath)
                        if srcpath_stat.st_ino == dstpath_stat.st_ino:
                            copy_info = "SKIPPING; correct file hardlink already exists"
                            proceed_with_copy = False
                        else:
                            copy_info = "SKIPPING; destination file already exists"
                            proceed_with_copy = False
                    else:
                        copy_info = "SKIPPING; destination file already exists"
                        proceed_with_copy = False

        if self.verbose:
            print("{}{}: {} -> {}{}".format(
                "(dryrun) " if self.dryrun else '', self.action_verb,
                srcpath, dstpath,
                " ({})".format(copy_info) if copy_info is not None else ''
            ))

        if not proceed_with_copy:
            return proceed_with_copy

        copy_shcmd_full = None
        if self.copy_shcmd is not None and proceed_with_copy:
            if self.copy_shcmd_is_fmtstr:
                copy_shcmd_full = self.copy_shcmd.format(srcpath, dstpath)
            elif self.reverse_args:
                copy_shcmd_full = "{} '{}' '{}'".format(self.copy_shcmd, dstpath, srcpath)
            else:
                copy_shcmd_full = "{} '{}' '{}'".format(self.copy_shcmd, srcpath, dstpath)

        if self.debug and proceed_with_copy:
            if copy_shcmd_full is not None:
                debug(copy_shcmd_full)
            else:
                debug("{}('{}', '{}')".format(self.copy_fn_name, srcpath, dstpath))

        if not self.dryrun and proceed_with_copy:

            if dstpath_stat is not None:
                if stat.S_ISDIR(dstpath_stat.st_mode) and overwrite_dir:
                    shutil.rmtree(dstpath)
                elif overwrite_file:
                    os.remove(dstpath)

            elif self.copy_makedirs:
                os.makedirs(os.path.dirname(dstpath), exist_ok=True)

            if copy_shcmd_full is not None:
                execute_shell_command(copy_shcmd_full)
            elif self.reverse_args:
                self.copy_fn(dstpath, srcpath)
            else:
                self.copy_fn(srcpath, dstpath)

        return proceed_with_copy


if psu_globals.SYSTYPE == psu_globals.SYSTYPE_WINDOWS:
    COPY_METHOD_HARDLINK_SYSTEM = CopyMethod('mklink /H', action_verb='hardlinking', reverse_args=True)
    COPY_METHOD_SYMLINK_SYSTEM = CopyMethod('mklink', action_verb='symlinking', reverse_args=True)
    COPY_METHOD_COPY_SYSTEM = CopyMethod('copy', action_verb='copying')
    COPY_METHOD_MOVE_SYSTEM = CopyMethod('move', action_verb='moving')
else:
    COPY_METHOD_HARDLINK_SYSTEM = CopyMethod('ln', action_verb='hardlinking')
    COPY_METHOD_SYMLINK_SYSTEM = CopyMethod('ln -s', action_verb='symlinking')
    COPY_METHOD_COPY_SYSTEM = CopyMethod('cp', action_verb='copying')
    COPY_METHOD_MOVE_SYSTEM = CopyMethod('mv', action_verb='moving')
COPY_METHOD_SHPROGS = set([cm.copy_shprog for cm in [
        COPY_METHOD_HARDLINK_SYSTEM,
        COPY_METHOD_SYMLINK_SYSTEM,
        COPY_METHOD_COPY_SYSTEM,
        COPY_METHOD_MOVE_SYSTEM
    ]])

try:
    COPY_METHOD_HARDLINK = CopyMethod(os.link, 'os.link', 'hardlinking')
    COPY_METHOD_SYMLINK = CopyMethod(os.symlink, 'os.symlink', 'symlinking')
except AttributeError:
    COPY_METHOD_HARDLINK = COPY_METHOD_HARDLINK_SYSTEM
    COPY_METHOD_SYMLINK = COPY_METHOD_SYMLINK_SYSTEM

COPY_METHOD_COPY_BASIC = CopyMethod(shutil.copyfile, 'shutil.copyfile', 'copying')
COPY_METHOD_COPY_PERMS = CopyMethod(shutil.copy, 'shutil.copy', 'copying')
COPY_METHOD_COPY_META = CopyMethod(shutil.copy2, 'shutil.copy2', 'copying')
COPY_METHOD_COPY_DEFAULT = COPY_METHOD_COPY_META

COPY_METHOD_MOVE = CopyMethod(shutil.move, 'shutil.move', 'moving')

COPY_METHOD_DICT = {
    'link': COPY_METHOD_HARDLINK,
    'hardlink': COPY_METHOD_HARDLINK,
    'symlink': COPY_METHOD_SYMLINK,
    'copy': COPY_METHOD_COPY_DEFAULT,
    'copy-basic': COPY_METHOD_COPY_BASIC,
    'copy-perms': COPY_METHOD_COPY_PERMS,
    'copy-meta': COPY_METHOD_COPY_META,
    'move': COPY_METHOD_MOVE,
}


##############################

### Argument globals ###

## Argument strings ("ARGSTR_")
ARGSTR_COPY_METHOD = '--copy-method'
ARGSTR_SYMLINK_FILES = '--symlink-files'
ARGSTR_MKDIR_UPON_FILE_COPY = '--mkdir-upon-file-copy'
ARGSTR_OVERWRITE_FILES = '--overwrite-files'
ARGSTR_OVERWRITE_DIRS = '--overwrite-dirs'
ARGSTR_OVERWRITE_DMATCH = '--overwrite-dmatch'

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
    ARGCHO_COPY_METHOD_COPY: COPY_METHOD_COPY_DEFAULT,
    ARGCHO_COPY_METHOD_MOVE: COPY_METHOD_MOVE,
    ARGCHO_COPY_METHOD_LINK: COPY_METHOD_HARDLINK,
    ARGCHO_COPY_METHOD_SYMLINK: COPY_METHOD_SYMLINK
}

## Argument defaults ("ARGDEF_")
ARGDEF_COPY_METHOD = ARGCHO_COPY_METHOD_COPY

##############################


def add_copymethod_arguments(parser,
                             copy_method=ARGDEF_COPY_METHOD):
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
        ARGSTR_SYMLINK_FILES,
        action='store_true',
        help=' '.join([
            "When {}={}, recurse into source folders and create symbolic links within the".format(ARGSTR_COPY_METHOD, ARGCHO_COPY_METHOD_SYMLINK),
            "destination directory pointing to the files within, instead of creating symbolic"
            "directory links within the destination pointing to source folders."
        ])
    )

    parser.add_argument(
        '-mufc', ARGSTR_MKDIR_UPON_FILE_COPY,
        action='store_true',
        # TODO: Write help string
        help="[write me]"
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

