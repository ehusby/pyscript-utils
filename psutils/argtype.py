
import functools
import operator
import os

import psutils.custom_errors as cerr

from psutils.globals import PATH_SEPARATORS_LIST
from psutils.string import endswith_one_of_coll

import psutils.string as psu_str


def access(path, mode, check_parent_if_dne=False):
    if not os.path.exists(path) and check_parent_if_dne:
        path_check_prev = ''
        path_check = os.path.realpath(path)
        while not os.path.isdir(path_check) and path_check != path_check_prev:
            path_check_prev = path_check
            path_check = os.path.dirname(path_check_prev)
    else:
        path_check = path
    return os.access(path_check, mode)


def argtype_bool_plus(value, parse_fn=None):
    if parse_fn is not None:
        return parse_fn(value)
    else:
        return value
ARGTYPE_BOOL_PLUS = functools.partial(functools.partial, argtype_bool_plus)


def argtype_path_handler(path, argstr,
                         append_prefix=None, append_suffix=None,
                         abspath_fn=os.path.realpath,
                         preserve_trailing_separator=True,
                         existcheck_fn=None, existcheck_reqval=None,
                         accesscheck_reqtrue=None, accesscheck_reqfalse=None,
                         accesscheck_parent_if_dne=False):

    if append_prefix is not None:
        path = append_prefix + path
    if append_suffix is not None:
        path = path + append_suffix
    path = os.path.expanduser(path)

    existcheck_fn_desc_dict = {
        os.path.isfile: 'file',
        os.path.isdir: 'directory',
        os.path.exists: 'file/directory'
    }
    pathtype_desc = existcheck_fn_desc_dict[existcheck_fn] if existcheck_fn else 'path'

    accesscheck_mode_desc_list = [
        [os.F_OK, 'existing'],
        [os.R_OK, 'readable'],
        [os.W_OK, 'writeable'],
        [os.X_OK, 'executable']
    ]

    if accesscheck_reqtrue is None:
        accesscheck_reqtrue = []
    if accesscheck_reqfalse is None:
        accesscheck_reqfalse = []
    if type(accesscheck_reqtrue) not in (set, tuple, list):
        accesscheck_reqtrue = [accesscheck_reqtrue]
    if type(accesscheck_reqfalse) not in (set, tuple, list):
        accesscheck_reqfalse = [accesscheck_reqfalse]

    accesscheck_reqtrue = set(accesscheck_reqtrue)
    accesscheck_reqfalse = set(accesscheck_reqfalse)
    modes_overlap = set(accesscheck_reqtrue).intersection(accesscheck_reqfalse)

    if len(modes_overlap) > 0:
        raise cerr.DeveloperError("The following permission settings (`os.access` modes)"
                             " appear in both required True and False lists: {}".format(modes_overlap))
    if existcheck_fn is not None and existcheck_fn(path) != existcheck_reqval:
        existresult_desc = 'does not exist' if existcheck_reqval is True else 'already exists'
        raise cerr.ScriptArgumentError("argument {} '{}': {} {}".format(argstr, path, pathtype_desc, existresult_desc))

    access_desc_reqtrue_list = [mode_descr for mode, mode_descr in accesscheck_mode_desc_list if mode in accesscheck_reqtrue]
    access_desc_reqfalse_list = [mode_descr for mode, mode_descr in accesscheck_mode_desc_list if mode in accesscheck_reqfalse]
    access_desc_reqtrue_err_list = [mode_descr for mode, mode_descr in accesscheck_mode_desc_list if mode in accesscheck_reqtrue and access(path, mode, accesscheck_parent_if_dne) is not True]
    access_desc_reqfalse_err_list = [mode_descr for mode, mode_descr in accesscheck_mode_desc_list if mode in accesscheck_reqfalse and access(path, mode, accesscheck_parent_if_dne) is not False]

    if len(access_desc_reqtrue_err_list) > 0 or len(access_desc_reqfalse_err_list) > 0:
        errmsg = ' '.join([
            "{} must".format(pathtype_desc),
            (len(access_desc_reqtrue_list) > 0)*"be ({})".format(' & '.join(access_desc_reqtrue_list)),
            "and" if (len(access_desc_reqtrue_list) > 0 and len(access_desc_reqfalse_list) > 0) else '',
            (len(access_desc_reqfalse_list) > 0)*"not be ({})".format(', '.join(access_desc_reqfalse_list)),
            ", but it",
            (len(access_desc_reqtrue_err_list) > 0)*"is not ({})".format(', '.join(access_desc_reqtrue_err_list)),
            "and" if (len(access_desc_reqtrue_err_list) > 0 and len(access_desc_reqfalse_err_list) > 0) else '',
            (len(access_desc_reqfalse_err_list) > 0)*"is ({})".format(', '.join(access_desc_reqfalse_err_list)),
        ])
        errmsg = ' '.join(errmsg.split())
        errmsg = errmsg.replace(' ,', ',')
        raise cerr.ScriptArgumentError("argument {} '{}': {}".format(argstr, path, errmsg))

    return_path = abspath_fn(path) if abspath_fn is not None else path
    if preserve_trailing_separator:
        if endswith_one_of_coll(path, PATH_SEPARATORS_LIST) and not endswith_one_of_coll(return_path, PATH_SEPARATORS_LIST):
            return_path = return_path+os.path.sep

    return return_path

ARGTYPE_PATH = functools.partial(functools.partial, argtype_path_handler)


def argtype_num_encode(num):
    num_str = str(num)
    if num_str.startswith('-') or num_str.startswith('+'):
        num_str = "'({})' ".format(num_str)
    return num_str

def argtype_num_decode(num_str):
    num_str = ''.join(num_str.split())
    return num_str.strip("'").strip('"').lstrip('(').rstrip(')')

def argtype_num_handler(num_str, argstr,
                        numeric_type=float,
                        allow_pos=True, allow_neg=True, allow_zero=True,
                        allow_inf=False, allow_nan=False,
                        allowed_min=None, allowed_max=None,
                        allowed_min_incl=True, allowed_max_incl=True):
    num_str = argtype_num_decode(num_str)

    if (   (allowed_min is not None and ((allowed_min < 0 and not allow_neg) or (allowed_min == 0 and not allow_zero) or (allowed_min > 0 and not allow_pos)))
        or (allowed_max is not None and ((allowed_max < 0 and not allow_neg) or (allowed_max == 0 and not allow_zero) or (allowed_max > 0 and not allow_pos)))):
        raise cerr.DeveloperError("Allowed min/max value does not align with allowed pos/neg/zero settings")

    dtype_name_dict = {
        int: 'integer',
        float: 'decimal'
    }

    lt_min_op = operator.lt if allowed_min_incl else operator.le
    gt_max_op = operator.gt if allowed_max_incl else operator.ge

    errmsg = None
    try:
        number_float = float(num_str)
    except ValueError:
        errmsg = "input could not be parsed as a valid (floating point) number"
    if errmsg is None:
        if number_float != number_float:  # assume number is NaN
            number_true = number_float
            if not allow_nan:
                errmsg = "NaN is not allowed"
        else:
            if number_float in (float('inf'), float('-inf')):
                number_true = number_float
                if not allow_inf:
                    errmsg = "+/-infinity is not allowed"
            else:
                try:
                    number_true = numeric_type(number_float)
                    if number_true != number_float:
                        errmsg = "number must be of {}type {}".format(
                            dtype_name_dict[numeric_type]+' ' if numeric_type in dtype_name_dict else '', numeric_type)
                except ValueError:
                    errmsg = "input could not be parsed as a designated {} number".format(numeric_type)
            if errmsg is None:
                if (   (not allow_pos and number_true > 0) or (not allow_neg and number_true < 0) or (not allow_zero and number_true == 0)
                    or (allowed_min is not None and lt_min_op(number_true, allowed_min)) or (allowed_max is not None and gt_max_op(number_true, allowed_max))):
                    input_cond = ' '.join([
                        "input must be a",
                        'positive'*allow_pos, 'or'*(allow_pos&allow_neg), 'negative'*allow_neg, 'non-zero'*(not allow_zero),
                        '{} number'.format(dtype_name_dict[numeric_type]) if numeric_type in dtype_name_dict else 'number of type {}'.format(numeric_type),
                        (allow_inf|allow_nan)*' ({} allowed)'.format(' '.join([
                            '{}infinity'.format('/'.join(['+'*allow_pos, '-'*allow_neg]).strip('/'))*allow_inf, 'and'*(allow_inf&allow_nan), 'NaN'*allow_nan]))
                    ])
                    if allowed_min is not None or allowed_max is not None:
                        if allowed_min is not None and allowed_max is not None:
                            input_cond_range = "in the range {}{}, {}{}".format(
                                '[' if allowed_min_incl else '(', allowed_min, allowed_max, ']' if allowed_max_incl else ']')
                        else:
                            if allowed_min is not None:
                                cond_comp = 'greater'
                                cond_value = allowed_min
                                cond_bound_incl = allowed_min_incl
                            elif allowed_max is not None:
                                cond_comp = 'less'
                                cond_value = allowed_max
                                cond_bound_incl = allowed_max_incl
                            input_cond_range = '{} than {} ({})'.format(
                                cond_comp, cond_value, 'inclusive' if cond_bound_incl else 'exclusive')
                        input_cond = ' '.join([input_cond, input_cond_range])
                    input_cond = ' '.join(input_cond.split())
                    input_cond = input_cond.replace(' ,', ',')
                    errmsg = input_cond

    if errmsg is not None:
        raise cerr.ScriptArgumentError("argument {} '{}': {}".format(argstr, num_str, errmsg))
    else:
        return number_true

ARGTYPE_NUM = functools.partial(functools.partial, argtype_num_handler)
ARGNUM_POS_INF = argtype_num_encode(float('inf'))
ARGNUM_NEG_INF = argtype_num_encode(float('-inf'))
ARGNUM_NAN = argtype_num_encode(float('nan'))


def argtype_duration_handler(dur_str, argstr):
    pass
ARGTYPE_DURATION = functools.partial(functools.partial, argtype_duration_handler)
