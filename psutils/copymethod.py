
import filecmp
import os
import shutil
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

        self.copy_overwrite = False
        self.dryrun = False
        self.verbose = True
        self.debug = False

    def __copy__(self):
        copy_method = CopyMethod(self.copy_fn, self.copy_fn_name, self.action_verb,
                                 self.reverse_args, self.copy_shcmd_is_fmtstr)
        copy_method.set_options(self.copy_overwrite, self.dryrun, self.verbose, self.debug)
        return copy_method

    def set_options(self, copy_overwrite=None, copy_dryrun=None, copy_verbose=None, copy_debug=None):
        if copy_overwrite is not None:
            self.copy_overwrite = copy_overwrite
        if copy_dryrun is not None:
            self.dryrun = copy_dryrun
        if copy_verbose is not None:
            self.verbose = copy_verbose
        if copy_debug is not None:
            self.debug = copy_debug

    def copy(self, srcfile, dstfile):
        copy_shcmd_full = None
        if self.copy_shcmd is not None:
            if self.copy_shcmd_is_fmtstr:
                copy_shcmd_full = self.copy_shcmd.format(srcfile, dstfile)
            elif self.reverse_args:
                copy_shcmd_full = "{} {} {}".format(self.copy_shcmd, dstfile, srcfile)
            else:
                copy_shcmd_full = "{} {} {}".format(self.copy_shcmd, srcfile, dstfile)

        dstfile_exists = os.path.isfile(dstfile)
        if dstfile_exists:
            if self.copy_overwrite:
                proceed_with_copy = True
                overwrite_action = "OVERWRITING"
            else:
                proceed_with_copy = False
                # dstfile_is_srcfile = filecmp.cmp(srcfile, dstfile) if self.action_verb in ['HARDLINKING', 'LINKING'] else False
                dstfile_is_srcfile = os.stat(srcfile).st_ino == os.stat(dstfile).st_ino if self.action_verb in ['HARDLINKING', 'LINKING'] else False
                if dstfile_is_srcfile:
                    overwrite_action = "SKIPPING; correct link already exists"
                else:
                    overwrite_action = "SKIPPING; destination file already exists"
        else:
            proceed_with_copy = True
            overwrite_action = ''

        if self.verbose:
            print("{}{}: {} -> {}{}".format(
                "(dryrun) " if self.dryrun else '', self.action_verb,
                srcfile, dstfile,
                " ({})".format(overwrite_action) if dstfile_exists else ''
            ))

        if not proceed_with_copy:
            return

        if self.debug and proceed_with_copy:
            if copy_shcmd_full is not None:
                print(copy_shcmd_full)
            else:
                print("{}({}, {})".format(self.copy_fn_name, srcfile, dstfile))

        if not self.dryrun and proceed_with_copy:
            if dstfile_exists and self.copy_overwrite:
                os.remove(dstfile)
            if copy_shcmd_full is not None:
                execute_shell_command(copy_shcmd_full)
            elif self.reverse_args:
                self.copy_fn(dstfile, srcfile)
            else:
                self.copy_fn(srcfile, dstfile)


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
