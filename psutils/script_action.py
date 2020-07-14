
import copy
from email.mime.text import MIMEText
import os
import platform
import smtplib
import subprocess
import traceback

import psutils.scheduler as psu_sched
from psutils.print_methods import *

from psutils import PYTHON_VERSION_REQUIRED_MIN
from psutils.tasklist import write_task_bundles
from psutils.string import get_index_fmtstr
from psutils.stream import capture_stdout_stderr


def send_email(to_addr, subject, body, from_addr=None):
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


def check_mut_excl_arggrp(args, argcol_mut_excl):
    for arggrp in argcol_mut_excl:
        if [args.get(argstr) is True if type(args.get(argstr)) is bool else
            args.get(argstr) is not None for argstr in arggrp].count(True) > 1:
            args.parser.error("{} arguments are mutually exclusive{}".format(
                "{} and {}".format(*arggrp) if len(arggrp) == 2 else "The following",
                '' if len(arggrp) == 2 else ": {}".format(arggrp)
            ))


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
    if child_args is None:
        child_args = copy.deepcopy(parent_args)
    child_args.unset(psu_sched.ARGGRP_SCHEDULER)

    child_tasks = (parent_tasks if parent_args.get(psu_sched.ARGSTR_TASKS_PER_JOB) is None else
        write_task_bundles(parent_tasks, parent_args.get(psu_sched.ARGSTR_TASKS_PER_JOB), parent_args.get(psu_sched.ARGSTR_BUNDLEDIR),
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
            subprocess.call(cmd, shell=True, cwd=parent_args.get(psu_sched.ARGSTR_LOGDIR))


def handle_task_exception(args, error):
    with capture_stdout_stderr() as out:
        traceback.print_exc()
    caught_out, caught_err = out
    error_trace = caught_err
    eprint(error_trace)
    if error.__class__ is ImportError:
        print(' '.join([
            "\nFailed to import necessary module(s)\n"
            "If running on a Linux system where the jobscripts/init.sh file has been properly",
            "set up, try running the following command to activate a working environment",
            "in your current shell session:\n{}\n".format("source {} {}".format(psu_sched.JOBSCRIPT_INIT, args.get(psu_sched.ARGSTR_JOB_ABBREV))),
        ]))


def send_script_completion_email(args, error_trace):
    email_body = args.script_run_cmd+'\n'
    if error_trace is not None:
        email_status = "ERROR"
        email_body += "\n{}\n".format(error_trace)
    else:
        email_status = "COMPLETE"
    email_subj = "{} - {}".format(email_status, args.script_fname)
    send_email(args.get(psu_sched.ARGSTR_EMAIL), email_subj, email_body)
