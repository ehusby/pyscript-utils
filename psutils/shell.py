
import shlex
import subprocess

import psutils.custom_errors as cerr
from psutils.print_methods import *


# TODO: See if it's possible to check a script called directly from
# -t    the PATH on Windows for a shebang to make sure it gets run
# -t    with the correct (Python) binary & environment.
def run_subprocess(cmd_str=None, cmd_token_list=None,
                   tokenize_cmd_str=False, shell=None,
                   executable=None, cwd=None, env=None,
                   bufsize=-1, encoding='utf-8',
                   stdin=None, stdout=None, stderr=None,
                   send_stderr_to_stdout=False, quiet=False,
                   return_streams=False, return_popen=False,
                   rclist_success=0, rclist_failure=True,
                   throw_exception_in_failure=True,
                   print_stderr_in_failure=True,
                   print_failure_info=True,
                   print_begin_info=False,
                   print_end_info=False,
                   print_cmd_in_info=True,
                   print_method=print,
                   eprint_method=eprint):
    if [arg is not None for arg in (cmd_str, cmd_token_list)].count(True) != 1:
        raise cerr.InvalidArgumentError("Only one of (`cmd_str`, `cmd_token_list`) arguments must be provide")
    if return_streams and return_popen:
        raise cerr.InvalidArgumentError("Only one of (`return_streams`, `return_popen`) arguments may be provided")

    args = None
    if cmd_str is not None:
        if tokenize_cmd_str:
            cmd_token_list = shlex.split(cmd_str)
            args = cmd_token_list
        else:
            args = cmd_str
    elif cmd_token_list is not None:
        cmd_str = shlex.join(cmd_token_list)
        args = cmd_token_list

    if shell is None:
        if type(args) is str:
            shell = True
        else:
            shell = False

    if quiet or return_streams:
        if stdout is None:
            stdout = subprocess.PIPE
        if stderr is None and not send_stderr_to_stdout:
            stderr = subprocess.PIPE
    if send_stderr_to_stdout:
        if stderr is not None:
            raise cerr.InvalidArgumentError("`stderr` argument must be None when `send_stderr_to_stdout` argument is True")
        stderr = subprocess.STDOUT

    proc = subprocess.Popen(args, bufsize=bufsize, executable=executable,
                            stdin=stdin, stdout=stdout, stderr=stderr,
                            shell=shell, cwd=cwd, env=env,
                            universal_newlines=True, encoding=encoding)
    proc_pid = proc.pid
    if print_begin_info:
        print_method("Beginning subprocess (PID={}){}".format(
            proc_pid,
            ': """ {} """'.format(cmd_str) if print_cmd_in_info else '')
        )

    stdout, stderr = proc.communicate()
    return_code = proc.returncode
    if not quiet:
        if stdout is not None:
            sys.stdout.write(stdout)
        if stderr is not None:
            sys.stderr.write(stderr)
            print_stderr_in_failure = False

    rc_success = None
    rc_failure = None
    if all(type(arg) in (type(None), bool) for arg in (rclist_success, rclist_failure)):
        rc_status = "ambiguous success/failure (no success/failure codes set)"
    elif type(rclist_success) not in (type(None), bool) and (return_code == rclist_success if type(rclist_success) is int else (return_code in rclist_success)):
        rc_status = "success (success={})".format(rclist_success)
        rc_success = True
    elif type(rclist_failure) not in (type(None), bool) and (return_code == rclist_failure if type(rclist_failure) is int else (return_code in rclist_failure)):
        rc_status = "failure (failure={})".format(rclist_failure)
        rc_failure = True
    elif rclist_success is True:
        rc_status = "ambiguous success (failure={})".format(rclist_failure)
        rc_success = True
    elif rclist_failure is True:
        rc_status = "ambiguous failure (success={})".format(rclist_success)
        rc_failure = True
    else:
        rc_status = "ambiguous success/failure (success={}, failure={})".format(rclist_success, rclist_failure)

    end_info = "Subprocess (PID={}) finished with return code (RC={}) indicating {}{}".format(
        proc_pid,
        return_code,
        rc_status,
        ': """ {} """'.format(cmd_str) if print_cmd_in_info else ''
    )
    printed_end_info = False

    if rc_failure:
        if throw_exception_in_failure:
            raise cerr.ExternalError(end_info)
        if print_stderr_in_failure and stderr is not None:
            sys.stderr.write(stderr)
        if print_failure_info:
            eprint_method(end_info)
            printed_end_info = True

    if print_end_info and not printed_end_info:
        print_method(end_info)

    if return_popen:
        return proc
    else:
        return (return_code, stdout, stderr) if return_streams else return_code
