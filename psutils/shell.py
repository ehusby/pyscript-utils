
import shlex
import subprocess

import psutils.custom_errors as cerr
from psutils.print_methods import *


def execute_shell_command(cmd_str=None, tokenize_cmd=False,
                          arg_list=[], shell=None,
                          cwd=None, env=None,
                          executable=None, bufsize=-1,
                          stdin=None, stdout=None, stderr=None,
                          send_stderr_to_stdout=False, quiet=False,
                          return_streams=False, return_popen=False,
                          success_error_codes=[0],
                          ignore_failure=False,
                          throw_exception_in_failure=True,
                          print_stderr_in_failure=True,
                          print_failure_info=False,
                          print_begin_info=False,
                          print_end_info=False):
    if [cmd_str is not None, len(arg_list) > 0].count(True) != 1:
        raise cerr.InvalidArgumentError("Only one of (`cmd_str`, `arg_list`) arguments must be provide")
    if return_streams and return_popen:
        raise cerr.InvalidArgumentError("Only one of (`return_streams`, `return_popen`) arguments may be provided")
    if cmd_str is not None:
        args = shlex.split(cmd_str) if tokenize_cmd else cmd_str
        if shell is None:
            shell = True
    else:
        args = arg_list
        if shell is None:
            shell = False
        cmd_str = ' '.join(arg_list)
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
                            universal_newlines=True)
    proc_pid = proc.pid
    if print_begin_info:
        print('Beginning external call (PID {}): """ {} """'.format(proc_pid, cmd_str))
    stdout, stderr = proc.communicate()
    return_code = proc.returncode
    if not quiet:
        if stdout is not None:
            sys.stdout.write(stdout)
        if stderr is not None:
            sys.stderr.write(stderr)
            print_stderr_in_failure = False
    if return_code not in success_error_codes and not ignore_failure:
        errmsg = 'External call (PID {}) failed with non-zero exit status ({}): """ {} """'.format(proc_pid, return_code, cmd_str)
        if throw_exception_in_failure:
            raise cerr.ExternalError(errmsg)
        if print_stderr_in_failure and stderr is not None:
            sys.stderr.write(stderr)
        if print_failure_info:
            eprint(print_failure_info)
    if print_end_info:
        print("External call (PID {}) completed successfully".format(proc_pid))
    if return_popen:
        return proc
    else:
        return (return_code, stdout, stderr) if return_streams else return_code
