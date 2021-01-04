
import os

import psutils.argtype as psu_at

from psutils import MODULE_DIR


##############################

### Argument globals ###

## Argument strings ("ARGSTR_")
ARGSTR_SCHEDULER = '--scheduler'
ARGSTR_JOBSCRIPT = '--jobscript'
ARGSTR_JOB_ABBREV = '--job-abbrev'
ARGSTR_JOB_WALLTIME = '--job-walltime'
ARGSTR_JOB_MEMORY = '--job-memory'
ARGSTR_TASKS_PER_JOB = '--tasks-per-job'
ARGSTR_JOB_BUNDLEDIR = '--job-bundledir'
ARGSTR_JOB_LOGDIR = '--job-logdir'
ARGSTR_EMAIL = '--email'

## Argument groups ("ARGGRP_" lists of "ARGSTR_" argument strings)
ARGGRP_SCHEDULER = [
    ARGSTR_SCHEDULER,
    ARGSTR_JOBSCRIPT,
    ARGSTR_JOB_ABBREV,
    ARGSTR_JOB_WALLTIME,
    ARGSTR_JOB_MEMORY,
    ARGSTR_TASKS_PER_JOB,
    ARGSTR_JOB_BUNDLEDIR,
    ARGSTR_JOB_LOGDIR,
    ARGSTR_EMAIL,
]
ARGGRP_OUTDIR = [
    ARGSTR_JOB_BUNDLEDIR,
    ARGSTR_JOB_LOGDIR
]

## Argument defaults ("ARGDEF_")
ARGDEF_BUNDLEDIR = os.path.realpath(os.path.join(os.path.expanduser('~'), 'scratch', 'task_bundles'))

##############################

### Custom globals ###

JOBSCRIPT_DIR = os.path.join(MODULE_DIR, 'jobscripts')
JOBSCRIPT_INIT = os.path.join(JOBSCRIPT_DIR, 'init.sh')

SCHED_SUPPORTED = []
SCHED_PBS = 'pbs'
SCHED_SLURM = 'slurm'
SCHED_NAME_TESTCMD_DICT = {
    SCHED_PBS: 'pbsnodes',
    SCHED_SLURM: 'sinfo'
}
# if SYSTYPE == SYSTYPE_LINUX:
#     for sched_name in sorted(SCHED_NAME_TESTCMD_DICT.keys()):
#         try:
#             proc = subprocess.Popen(SCHED_NAME_TESTCMD_DICT[sched_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
#             if proc.wait() == 0:
#                 SCHED_SUPPORTED.append(sched_name)
#         except OSError:
#             pass
if len(SCHED_SUPPORTED) == 0:
    SCHED_SUPPORTED.append(None)

##############################


def add_scheduler_arguments(parser,
                            job_abbrev,
                            job_walltime,
                            job_memory,
                            bundledir=ARGDEF_BUNDLEDIR):
    parser.add_argument(
        ARGSTR_SCHEDULER,
        type=str,
        choices=SCHED_SUPPORTED,
        default=None,
        help="Name of job scheduler to use for task submission."
    )
    parser.add_argument(
        '-ja', ARGSTR_JOB_ABBREV,
        type=str,
        default=job_abbrev,
        help="Prefix for the jobnames of jobs submitted to scheduler."
    )
    parser.add_argument(
        '-jw', ARGSTR_JOB_WALLTIME,
        type=psu_at.ARGTYPE_NUM(argstr=ARGSTR_JOB_WALLTIME,
            numeric_type=int, allow_neg=False, allow_zero=False, allow_inf=False),
        default=job_walltime,
        help="Wallclock time alloted for each job submitted to scheduler."
    )
    parser.add_argument(
        '-jm', ARGSTR_JOB_MEMORY,
        type=psu_at.ARGTYPE_NUM(argstr=ARGSTR_JOB_MEMORY,
            numeric_type=int, allow_neg=False, allow_zero=False, allow_inf=False),
        default=job_memory,
        help="Memory alloted for each job submitted to scheduler."
    )
    parser.add_argument(
        '-js', ARGSTR_JOBSCRIPT,
        type=psu_at.ARGTYPE_PATH(argstr=ARGSTR_JOBSCRIPT,
            existcheck_fn=os.path.isfile,
            existcheck_reqval=True,
            accesscheck_reqtrue=os.W_OK,
            accesscheck_parent_if_dne=True),
        default=None,
        help=' '.join([
            "Script to run in job submission to scheduler.",
            "(default scripts are found in {})".format(JOBSCRIPT_DIR),
        ])
    )
    parser.add_argument(
        '-tpj', ARGSTR_TASKS_PER_JOB,
        type=psu_at.ARGTYPE_NUM(argstr=ARGSTR_JOB_MEMORY,
            numeric_type=int, allow_neg=False, allow_zero=False, allow_inf=False),
        default=None,
        help=' '.join([
            "Number of tasks to bundle into a single job.",
            "(requires {} option)".format(ARGSTR_SCHEDULER),
        ])
    )
    parser.add_argument(
        '-jbd', ARGSTR_JOB_BUNDLEDIR,
        type=psu_at.ARGTYPE_PATH(argstr=ARGSTR_JOB_BUNDLEDIR,
            existcheck_fn=os.path.isfile,
            existcheck_reqval=False,
            accesscheck_reqtrue=os.W_OK,
            accesscheck_parent_if_dne=True),
        default=bundledir,
        help=' '.join([
            "Directory in which task bundle textfiles will be built if {} option is provided".format(ARGSTR_TASKS_PER_JOB),
            "for job submission to scheduler.",
        ])
    )
    parser.add_argument(
        '-jld', ARGSTR_JOB_LOGDIR,
        type=psu_at.ARGTYPE_PATH(argstr=ARGSTR_JOB_LOGDIR,
            existcheck_fn=os.path.isfile,
            existcheck_reqval=False,
            accesscheck_reqtrue=os.W_OK,
            accesscheck_parent_if_dne=True),
        default=None,
        help=' '.join([
            "Directory to which standard output/error log files will be written for batch job runs.",
            "\nIf not provided, default scheduler (or jobscript #CONDOPT_) options will be used.",
            "\n**Note:** Due to implementation difficulties, this directory will also become the",
            "working directory for job processes.",
        ])
    )
    parser.add_argument(
        '-m', ARGSTR_EMAIL,
        type=psu_at.ARGTYPE_BOOL_PLUS(
            parse_fn=str),
        nargs='?',
        help="Send email to user upon end or abort of the LAST SUBMITTED task."
    )
