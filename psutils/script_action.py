
import argparse
import copy
from datetime import datetime
from email.mime.text import MIMEText
import getpass
import os
import platform
import smtplib
import subprocess
import traceback

import psutils.custom_errors as cerr
import psutils.globals as psu_globals
import psutils.scheduler as psu_sched
from psutils.print_methods import *

from psutils import PYTHON_VERSION_REQUIRED_MIN
from psutils.stream import capture_stdout_stderr
from psutils.func import with_noop


##############################

### Argument globals ###

## Argument strings ("ARGSTR_")
ARGSTR_EMAIL = '--email'
ARGSTR_QUIET = '--quiet'
ARGSTR_DEBUG = '--debug'
ARGSTR_DRYRUN = '--dryrun'

##############################


def add_action_arguments(parser):
    try:
        parser.add_argument(
            '-m', ARGSTR_EMAIL,
            type=str,
            help="Email address to send notice to upon script completion."
        )
    except argparse.ArgumentError:
        pass
    parser.add_argument(
        '-q', ARGSTR_QUIET,
        action='store_true',
        # TODO: Write help string
        help="[write me]"
    )
    parser.add_argument(
        '-db', ARGSTR_DEBUG,
        action='store_true',
        # TODO: Write help string
        help="[write me]"
    )
    parser.add_argument(
        '-dr', ARGSTR_DRYRUN,
        action='store_true',
        help="Print actions without executing."
    )


def get_preamble(args=None, sys_argv=None):
    if sys_argv is None:
        sys_argv = sys.argv
    script_preamble = """
________________________________________________________
________________________________________________________

Python Script Log

Start time: {}
Process ID: {}
Submitted by user: {}
Running on system: {}

Script path: {}
Working dir: {}

--- Script arguments (sys.argv) ---
{}

--- ArgumentPasser command ---
{}
________________________________________________________
""".format(
        datetime.now(),
        os.getpid(),
        getpass.getuser(),
        platform.platform(),
        args.script_file,
        os.getcwd(),
        ' '.join(sys_argv),
        args.get_cmd().replace('\\', '\\\\')
    ).lstrip()
    return script_preamble


def setup_outfile_logging(args):
    import psutils.log as psu_log

    log_outfile, log_errfile = args.get(psu_log.ARGSTR_LOG_OUTFILE, psu_log.ARGSTR_LOG_ERRFILE)

    if log_outfile is None and log_errfile is None:
        return

    if log_outfile is not None and log_errfile is None:
        log_errfile = log_outfile

    logging_level = psu_log.ARGMAP_LOG_LEVEL[args.get(psu_log.ARGSTR_LOG_LEVEL)]
    file_handler_mode = psu_log.ARGMAP_LOG_MODE_FH_MODE[args.get(psu_log.ARGSTR_LOG_MODE)]

    psu_logger_level = psu_log.get_logger_level()
    if logging_level < psu_logger_level:
        psu_log.set_stream_handler_level(psu_logger_level)

    psu_log.setup_log_files(
        logger_level=logging_level, handler_level=logging_level,
        file_out=log_outfile, file_err=log_errfile,
        file_handler_mode=file_handler_mode
    )


def get_script_arg_values(argstr, nvals=1, dtype=str, list_single_value=False):
    values = []
    for i, arg in enumerate(sys.argv):
        if arg == argstr:
            argval_i_start = i + 1
            argval_i_end = argval_i_start + nvals
            if argval_i_end <= len(sys.argv):
                values.extend([dtype(val) for val in sys.argv[argval_i_start:argval_i_end]])
    if len(values) == 0:
        values = None
    elif len(values) == 1 and not list_single_value:
        values = values[0]
    return values


def apply_argument_settings(args, argset_flags, argset_choices):

    for flag_argstr, flag_settings in argset_flags:
        if args.get(flag_argstr) is True:
            for set_argstr, set_value in flag_settings:
                old_value = args.get(set_argstr)
                if args.provided(set_argstr) and old_value is not None and old_value != set_value:
                    args.parser.error(
                        "{} and {}='{}' arguments are mutually exclusive".format(
                            flag_argstr, set_argstr, old_value))
                args.set(set_argstr, set_value)

    for choice_argstr, choice_settings_dict in argset_choices:
        choice_value = args.get(choice_argstr)
        if choice_value in choice_settings_dict:
            choice_settings = choice_settings_dict[choice_value]
            for set_argstr, set_value in choice_settings:
                old_value = args.get(set_argstr)
                if args.provided(set_argstr) and old_value is not None and old_value != set_value:
                    args.parser.error(
                        "{}='{}' and {}='{}' arguments are mutually exclusive".format(
                            choice_argstr, choice_value, set_argstr, old_value))
                args.set(set_argstr, set_value)


def set_default_jobscript(args):
    if args.get(psu_sched.ARGSTR_SCHEDULER) is not None:
        if args.get(psu_sched.ARGSTR_JOBSCRIPT) is None:
            jobscript_default = os.path.join(psu_sched.JOBSCRIPT_DIR, 'head_{}.sh'.format(args.get(psu_sched.ARGSTR_SCHEDULER)))
            if not os.path.isfile(jobscript_default):
                args.parser.error(
                    "Default jobscript ({}) does not exist, ".format(jobscript_default)
                    + "please specify one with {} argument".format(psu_sched.ARGSTR_JOBSCRIPT))
            else:
                args.set(psu_sched.ARGSTR_JOBSCRIPT, jobscript_default)
                print("argument {} set automatically to: {}".format(psu_sched.ARGSTR_JOBSCRIPT, args.get(psu_sched.ARGSTR_JOBSCRIPT)))


def flatten_nargs_plus_action_append_lists(args, *argstrs):
    for item in argstrs:
        argstr_list = [item] if type(item) is str else item
        for argstr in argstr_list:
            if args.get(argstr) is not None:
                arg_list_combined = []
                for src_list in args.get(argstr):
                    arg_list_combined.extend(src_list)
                args.set(argstr, arg_list_combined)


def check_mutually_exclusive_args(args, argcol_mut_excl_set, argcol_mut_excl_provided):

    for arggrp in argcol_mut_excl_set:
        if [args.get(argstr) is True if type(args.get(argstr)) is bool else
            args.get(argstr) is not None for argstr in arggrp].count(True) > 1:
            args.parser.error("{} arguments are mutually exclusive{}".format(
                "{} and {}".format(*arggrp) if len(arggrp) == 2 else "The following",
                '' if len(arggrp) == 2 else ": {}".format(arggrp)
            ))

    for arggrp in argcol_mut_excl_provided:
        if [args.provided(argstr) for argstr in arggrp].count(True) > 1:
            args.parser.error("{} arguments are mutually exclusive{}".format(
                "{} and {}".format(*arggrp) if len(arggrp) == 2 else "The following",
                '' if len(arggrp) == 2 else ": {}".format(arggrp)
            ))


def parse_args(python_exe, script_file, arg_parser, sys_argv,
               doubled_args=dict(), doubled_args_restricted_optgrp=None):
    from psutils.argumentpasser import ArgumentPasser

    args = ArgumentPasser(python_exe, script_file, arg_parser, sys_argv, remove_args=[], parse=False)

    if doubled_args is None:
        doubled_args = dict()
    removable_args_opt = list(doubled_args.keys())
    removable_args_pos = list(doubled_args.values())

    removable_args = removable_args_pos if len(removable_args_pos) > 0 else None

    remove_args = None
    if removable_args is None:
        try_removing_args = False
        stream_capture_func = with_noop
    else:
        try_removing_args = True
        stream_capture_func = capture_stdout_stderr

    while True:
        try:
            with stream_capture_func() as _:
                args.parse()
            if removable_args is not None and remove_args is None:
                if len(set(removable_args_opt).intersection(args.provided_opt_args)) > 0:
                    raise cerr.ScriptArgumentError(
                        "positional arguments {} cannot be mixed with their counterpart "
                        "optional arguments {}".format(removable_args_pos, removable_args_opt))
                if doubled_args_restricted_optgrp is not None:
                    for arggrp_desc, arggrp in doubled_args_restricted_optgrp.items():
                        if len(set(arggrp).intersection(args.provided_opt_args)) > 0:
                            raise cerr.ScriptArgumentError(
                                "positional arguments {} cannot be mixed with '{}' type "
                                "optional arguments {}".format(removable_args_pos, arggrp_desc, arggrp))
            return args
        except cerr.ScriptArgumentError as e:
            arg_parser.error(str(e))
        except SystemExit as e:
            if try_removing_args and remove_args is not removable_args:
                remove_args = removable_args
                stream_capture_func = with_noop
                args.remove_args(remove_args)
            else:
                raise


def create_argument_directories(args, *dir_argstrs):
    dir_argstrs_unpacked = []
    for argstr in dir_argstrs:
        if type(argstr) in (tuple, list):
            dir_argstrs_unpacked.extend(list(argstr))
    for dir_argstr, dir_path in list(zip(dir_argstrs_unpacked, args.get_as_list(dir_argstrs_unpacked))):
        if dir_path is not None and not os.path.isdir(dir_path):
            print("Creating argument {} directory: {}".format(dir_argstr, dir_path))
            os.makedirs(dir_path)


def submit_tasks_to_scheduler(parent_args, parent_tasks,
                              parent_task_argstrs, child_bundle_argstr,
                              child_args=None,
                              task_items_descr=None, task_delim=',',
                              python_version_accepted_min=PYTHON_VERSION_REQUIRED_MIN,
                              dryrun=False):
    from psutils.tasklist import write_task_bundles
    from psutils.string import get_index_fmtstr

    if child_args is None:
        child_args = copy.deepcopy(parent_args)
    child_args.unset(psu_sched.ARGGRP_SCHEDULER)

    child_tasks = (parent_tasks if parent_args.get(psu_sched.ARGSTR_TASKS_PER_JOB) is None else
        write_task_bundles(parent_tasks, parent_args.get(psu_sched.ARGSTR_TASKS_PER_JOB), parent_args.get(psu_sched.ARGSTR_JOB_BUNDLEDIR),
            '{}_{}'.format(parent_args.get(psu_sched.ARGSTR_JOB_ABBREV),
                           task_items_descr if task_items_descr is not None else child_bundle_argstr.lstrip('-')),
            task_delim=task_delim)
    )
    child_task_argstrs = parent_task_argstrs if child_tasks is parent_tasks else child_bundle_argstr

    job_abbrev, job_walltime_hr, job_memory_gb = parent_args.get(psu_sched.ARGSTR_JOB_ABBREV, psu_sched.ARGSTR_JOB_WALLTIME, psu_sched.ARGSTR_JOB_MEMORY)
    jobname_fmt = job_abbrev+get_index_fmtstr(len(child_tasks))

    last_job_email = parent_args.get(psu_sched.ARGSTR_EMAIL)

    job_num = 0
    num_jobs = len(child_tasks)
    for task_items in child_tasks:
        job_num += 1

        child_args.set(child_task_argstrs, task_items)
        if job_num == num_jobs and last_job_email:
            child_args.set(psu_sched.ARGSTR_EMAIL, last_job_email)
        cmd_single = child_args.get_cmd()

        job_name = jobname_fmt.format(job_num)
        cmd = child_args.get_jobsubmit_cmd(
            parent_args.get(psu_sched.ARGSTR_SCHEDULER),
            jobscript=parent_args.get(psu_sched.ARGSTR_JOBSCRIPT),
            jobname=job_name, time_hr=job_walltime_hr, memory_gb=job_memory_gb, email=parent_args.get(psu_sched.ARGSTR_EMAIL),
            envvars=[parent_args.get(psu_sched.ARGSTR_JOBSCRIPT), job_abbrev, cmd_single, python_version_accepted_min]
        )

        print(cmd)
        if not dryrun:
            subprocess.call(cmd, shell=True, cwd=parent_args.get(psu_sched.ARGSTR_JOB_LOGDIR))


def handle_task_exception(args, error):
    with capture_stdout_stderr() as out:
        traceback.print_exc()
    caught_out, caught_err = out
    error_trace = caught_err
    eprint("Caught the following exception during script task execution\n{}".format(error_trace))
    if error.__class__ is ImportError:
        print(' '.join([
            "\nFailed to import necessary module(s)\n"
            "If running on a Linux system where the jobscripts/init.sh file has been properly",
            "set up, try running the following command to activate a working environment",
            "in your current shell session:\n{}\n".format("source {} {}".format(psu_sched.JOBSCRIPT_INIT, args.get(psu_sched.ARGSTR_JOB_ABBREV))),
        ]))
    return error_trace


def send_email(to_addr, subject, body, from_addr=None):
    from psutils.shell import execute_shell_command

    if psu_globals.SYSTYPE == psu_globals.SYSTYPE_WINDOWS:
        if from_addr is None:
            platform_node = platform.node()
            from_addr = platform_node if platform_node is not None else 'your-computer'
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = from_addr
        msg['To'] = to_addr
        s = smtplib.SMTP('localhost')
        s.sendmail(to_addr, [to_addr], msg.as_string())
        s.quit()

    else:
        mail_cmd = """ echo "{}" | mail -s "{}" {} """.format(body, subject, to_addr)
        execute_shell_command(mail_cmd)


def send_script_completion_email(args, error_trace):
    email_body = args.script_run_cmd+'\n'
    if error_trace is not None:
        email_status = "ERROR"
        email_body += "\n{}\n".format(error_trace)
    else:
        email_status = "COMPLETE"
    email_subj = "{} - {}".format(email_status, args.script_fname)
    send_email(args.get(psu_sched.ARGSTR_EMAIL), email_subj, email_body)
