
import argparse
import copy
import os
import sys

import psutils.custom_errors as cerr

from psutils.scheduler import SCHED_PBS, SCHED_SLURM


class RawTextArgumentDefaultsHelpFormatter(argparse.ArgumentDefaultsHelpFormatter, argparse.RawTextHelpFormatter): pass

class CustomArgumentParser(argparse.ArgumentParser):
    suppress_argument_error = False
    def error(self, message):
        """error(message: string)

        Prints a usage message incorporating the message to stderr and
        exits.

        If you override this in a subclass, it should not return -- it
        should either exit or raise an exception.
        """
        self.print_usage(sys.stderr)
        args = {'prog': self.prog, 'message': message}
        self.exit(2, _('%(prog)s: error: %(message)s\n') % args)

class ArgumentPasser(object):

    def __init__(self, executable_path, script_file, parser, sys_argv=[''], remove_args=[], parse=True):
        self.exe = executable_path
        self.script_file = script_file
        self.script_fname = os.path.basename(script_file)
        self.parser = parser
        self.sys_argv = list(sys_argv)
        self.script_run_cmd = ' '.join(self.sys_argv)
        self.parsed = parse

        if remove_args is None or (type(remove_args) is list and len(remove_args) == 0):
            pass
        else:
            if type(remove_args) is str:
                remove_args = [remove_args]
            argstr2varstr = self._make_argstr2varstr_dict()
            varstr2action = self._make_varstr2action_dict()
            for remove_argstr in remove_args:
                remove_action = varstr2action[argstr2varstr[remove_argstr]]
                self.parser._remove_action(remove_action)

        self.argstr_pos = self._find_pos_args()
        self.argstr2varstr = self._make_argstr2varstr_dict()
        self.varstr2argstr = self._make_varstr2argstr_dict()
        self.varstr2action = self._make_varstr2action_dict()
        self.provided_opt_args = self._find_provided_opt_args()

        if parse:
            self.vars = self.parser.parse_args()
            self.vars_dict = vars(self.vars)
        else:
            self.vars = None
            self.vars_dict = {varstr: None for varstr in self.varstr2argstr}

        self._fix_bool_plus_args()

        self.cmd_optarg_base = None
        self.cmd = None
        self._update_cmd_base()

    def __deepcopy__(self, memodict):
        args = ArgumentPasser(self.exe, self.script_file, self.parser, self.sys_argv, self.parsed)
        args.vars_dict = copy.deepcopy(self.vars_dict)
        return args

    def get_as_list(self, *argstrs):
        if len(argstrs) < 1:
            raise cerr.InvalidArgumentError("One or more argument strings must be provided")
        elif len(argstrs) == 1 and type(argstrs[0]) in (tuple, list):
            argstrs = argstrs[0]
        argstrs_invalid = set(argstrs).difference(set(self.argstr2varstr))
        if argstrs_invalid:
            raise cerr.InvalidArgumentError("This {} object does not have the following "
                                       "argument strings: {}".format(type(self).__name__, list(argstrs_invalid)))
        values = [self.vars_dict[self.argstr2varstr[argstr]] for argstr in argstrs]
        return values

    def get(self, *argstrs):
        values = self.get_as_list(*argstrs)
        if len(values) == 1:
            values = values[0]
        return values

    def set(self, argstrs, newval=None):
        if type(argstrs) in (tuple, list) and type(newval) in (tuple, list) and len(argstrs) == len(newval):
            argstr_list = argstrs
            for argstr_i, newval_i in list(zip(argstrs, newval)):
                if argstr_i not in self.argstr2varstr:
                    raise cerr.InvalidArgumentError("This {} object has no '{}' argument string".format(type(self).__name__, argstr_i))
                self.vars_dict[self.argstr2varstr[argstr_i]] = newval_i
        else:
            argstr_list = argstrs if type(argstrs) in (tuple, list) else [argstrs]
            for argstr in argstr_list:
                if argstr not in self.argstr2varstr:
                    raise cerr.InvalidArgumentError("This {} object has no '{}' argument string".format(type(self).__name__, argstr))
                if newval is None:
                    action = self.varstr2action[self.argstr2varstr[argstr]]
                    acttype = type(action)
                    if acttype is argparse._StoreAction and 'function argtype_bool_plus' in str(action.type):
                        newval = True
                    elif acttype in (argparse._StoreTrueAction, argparse._StoreFalseAction):
                        newval = (acttype is argparse._StoreTrueAction)
                    else:
                        raise cerr.InvalidArgumentError("Setting non-boolean argument string '{}' requires "
                                                   "a non-None `newval` value".format(argstr))
                self.vars_dict[self.argstr2varstr[argstr]] = newval
        if set(argstr_list).issubset(set(self.argstr_pos)):
            self._update_cmd()
        else:
            self._update_cmd_base()

    def unset(self, *argstrs):
        if len(argstrs) < 1:
            raise cerr.InvalidArgumentError("One or more argument strings must be provided")
        elif len(argstrs) == 1 and type(argstrs[0]) in (tuple, list):
            argstrs = argstrs[0]
        for argstr in argstrs:
            action = self.varstr2action[self.argstr2varstr[argstr]]
            acttype = type(action)
            if acttype is argparse._StoreAction and 'function argtype_bool_plus' in str(action.type):
                newval = False
            elif acttype in (argparse._StoreTrueAction, argparse._StoreFalseAction):
                newval = (acttype is argparse._StoreFalseAction)
            else:
                newval = None
            self.vars_dict[self.argstr2varstr[argstr]] = newval
        if set(argstrs).issubset(set(self.argstr_pos)):
            self._update_cmd()
        else:
            self._update_cmd_base()

    def provided(self, argstr):
        return argstr in self.provided_opt_args

    def _make_argstr2action_dict(self):
        argstr2action = {}
        for act in reversed(self.parser._actions):
            if len(act.option_strings) == 0:
                argstr = act.dest.replace('_', '-')
                argstr2action[argstr] = act
            else:
                for argstr in act.option_strings:
                    argstr2action[argstr] = act
        return argstr2action

    def _make_argstr2varstr_dict(self):
        argstr2varstr = {}
        for act in reversed(self.parser._actions):
            if len(act.option_strings) == 0:
                argstr = act.dest.replace('_', '-')
                argstr2varstr[argstr] = act.dest
            else:
                for argstr in act.option_strings:
                    argstr2varstr[argstr] = act.dest
        return argstr2varstr

    def _make_varstr2argstr_dict(self):
        varstr2argstr = {}
        for act in reversed(self.parser._actions):
            if len(act.option_strings) == 0:
                argstr = act.dest.replace('_', '-')
            else:
                argstr = max(act.option_strings, key=len)
            varstr2argstr[act.dest] = argstr
        return varstr2argstr

    def _make_varstr2action_dict(self):
        return {act.dest: act for act in reversed(self.parser._actions)}

    def _find_pos_args(self):
        return [act.dest.replace('_', '-') for act in self.parser._actions if len(act.option_strings) == 0]

    def _find_provided_opt_args(self):
        provided_opt_args = []
        for token in self.sys_argv:
            potential_argstr = token.split('=')[0]
            if potential_argstr in self.argstr2varstr:
                provided_opt_args.append(self.varstr2argstr[self.argstr2varstr[potential_argstr]])
        return provided_opt_args

    def _fix_bool_plus_args(self):
        for varstr in self.vars_dict:
            argstr = self.varstr2argstr[varstr]
            action = self.varstr2action[varstr]
            if 'function argtype_bool_plus' in str(action.type) and self.get(argstr) is None:
                self.set(argstr, (argstr in self.provided_opt_args))

    def _argval2str(self, item):
        if type(item) is str:
            if item.startswith('"') and item.endswith('"'):
                item_str = item
            elif item.startswith("'") and item.endswith("'"):
                item_str = item
            else:
                item_str = '"{}"'.format(item)
        else:
            item_str = '{}'.format(item)
        return item_str

    def _update_cmd_base(self):
        arg_list = []
        for varstr, val in self.vars_dict.items():
            argstr = self.varstr2argstr[varstr]
            if argstr not in self.argstr_pos and val is not None:
                if isinstance(val, bool):
                    action = self.varstr2action[varstr]
                    acttype = type(action)
                    if acttype is argparse._StoreAction:
                        if 'function argtype_bool_plus' in str(action.type) and val is True:
                            arg_list.append(argstr)
                    elif (   (acttype is argparse._StoreTrueAction and val is True)
                          or (acttype is argparse._StoreFalseAction and val is False)):
                        arg_list.append(argstr)
                elif isinstance(val, list) or isinstance(val, tuple):
                    arg_list.append('{} {}'.format(argstr, ' '.join([self._argval2str(item) for item in val])))
                else:
                    arg_list.append('{} {}'.format(argstr, self._argval2str(val)))
        self.cmd_optarg_base = ' '.join(arg_list)
        self._update_cmd()

    def _update_cmd(self):
        posarg_list = []
        for argstr in self.argstr_pos:
            varstr = self.argstr2varstr[argstr]
            val = self.vars_dict[varstr]
            if val is not None:
                if isinstance(val, list) or isinstance(val, tuple):
                    posarg_list.append(' '.join([self._argval2str(item) for item in val]))
                else:
                    posarg_list.append(self._argval2str(val))
        self.cmd = '{} {} {} {}'.format(self.exe, self.script_file, " ".join(posarg_list), self.cmd_optarg_base)

    def get_cmd(self):
        return self.cmd

    def get_jobsubmit_cmd(self, scheduler,
                          jobscript=None, jobname=None,
                          time_hr=None, time_min=None, time_sec=None,
                          memory_gb=None, node=None, email=None,
                          envvars=None):
        cmd = None
        cmd_envvars = None
        jobscript_optkey = None

        total_sec = 0
        if time_hr is not None:
            total_sec += time_hr*3600
        if time_min is not None:
            total_sec += time_min*60
        if time_sec is not None:
            total_sec += time_sec

        if total_sec == 0:
            time_hms = None
        else:
            m, s = divmod(total_sec, 60)
            h, m = divmod(m, 60)
            time_hms = '{:d}:{:02d}:{:02d}'.format(h, m, s)

        if envvars is not None:
            if type(envvars) in (tuple, list):
                cmd_envvars = ','.join(['p{}="{}"'.format(i, a) for i, a in enumerate(envvars)])
            elif type(envvars) == dict:
                cmd_envvars = ','.join(['{}="{}"'.format(var_name, var_val) for var_name, var_val in envvars.items()])

        if scheduler == SCHED_PBS:
            cmd = ' '.join([
                'qsub',
                "-N {}".format(jobname) * (jobname is not None),
                "-l {}".format(
                    ','.join([
                        "nodes={}".format(node) if node is not None else '',
                        "walltime={}".format(time_hms) if time_hms is not None else '',
                        "mem={}gb".format(memory_gb) if memory_gb is not None else ''
                    ]).strip(',')
                ) if (time_hms is not None and memory_gb is not None) else '',
                "-v {}".format(cmd_envvars) if cmd_envvars is not None else ''
                "-m ae" if email else ''
            ])
            jobscript_optkey = '#PBS'

        elif scheduler == SCHED_SLURM:
            cmd = ' '.join([
                'sbatch',
                "--job-name {}".format(jobname) if jobname is not None else '',
                "--time {}".format(time_hms) if time_hms is not None else '',
                "--mem {}G".format(memory_gb) if memory_gb is not None else '',
                "-v {}".format(cmd_envvars) if cmd_envvars is not None else ''
                "--mail-type FAIL,END" if email else '',
                "--mail-user {}".format(email) if type(email) is str else None
            ])
            jobscript_optkey = '#SBATCH'

        if jobscript_optkey is not None:
            jobscript_condoptkey = jobscript_optkey.replace('#', '#CONDOPT_')

            jobscript_condopts = []
            with open(jobscript) as job_script_fp:
                for line_num, line in enumerate(job_script_fp.readlines(), 1):
                    if line.lstrip().startswith(jobscript_condoptkey):

                        cond_ifval = None
                        cond_cond = None
                        cond_elseval = None

                        cond_remain = line.replace(jobscript_condoptkey, '').strip()
                        cond_parts = [s.strip() for s in cond_remain.split(' ELSE ')]
                        if len(cond_parts) == 2:
                            cond_remain, cond_elseval = cond_parts
                        cond_parts = [s.strip() for s in cond_remain.split(' IF ')]
                        if len(cond_parts) == 2:
                            cond_ifval, cond_cond = cond_parts

                        try:
                            condopt_add = None

                            if cond_ifval is not None and cond_cond is not None:
                                if self._jobscript_condopt_eval(cond_cond, eval):
                                    condopt_add = self._jobscript_condopt_eval(cond_ifval, str)
                                elif cond_elseval is not None:
                                    condopt_add = self._jobscript_condopt_eval(cond_elseval, str)
                            elif cond_elseval is not None:
                                raise SyntaxError
                            elif cond_remain.startswith('import') or cond_remain.startswith('from'):
                                exec(cond_remain)
                            else:
                                condopt_add = self._jobscript_condopt_eval(cond_remain, str)

                            if condopt_add is not None:
                                jobscript_condopts.append(condopt_add)

                        except SyntaxError:
                            raise cerr.InvalidArgumentError(' '.join([
                                "Invalid syntax in jobscript conditional option:",
                                "\n  File '{}', line {}: '{}'".format(jobscript, line_num, line.rstrip()),
                                "\nProper conditional option syntax is as follows:",
                                "'{} <options> [IF <conditional> [ELSE <options>]]'".format(jobscript_condoptkey)
                            ]))

            if jobscript_condopts:
                cmd = r'{} {}'.format(cmd, ' '.join(jobscript_condopts))

        cmd = r'{} "{}"'.format(cmd, jobscript)

        return cmd

    def _jobscript_condopt_eval(self, condopt_expr, out_type):
        if out_type not in (str, eval):
            raise cerr.InvalidArgumentError("`out_type` must be either str or eval")
        vars_dict = self.vars_dict
        for varstr in sorted(vars_dict.keys(), key=len, reverse=True):
            possible_substr = {'%'+s for s in [varstr, self.varstr2argstr[varstr], self.varstr2argstr[varstr].lstrip('-')]}
            possible_substr = possible_substr.union({s.lower() for s in possible_substr}, {s.upper() for s in possible_substr})
            for substr in possible_substr:
                if substr in condopt_expr:
                    replstr = str(vars_dict[varstr]) if out_type is str else "vars_dict['{}']".format(varstr)
                    condopt_expr = condopt_expr.replace(substr, replstr)
                    break
        return out_type(condopt_expr)
