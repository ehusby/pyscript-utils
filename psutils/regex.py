
import re

import psutils.custom_errors as cerr


class RegexConstructionFailure(Exception):
    def __init__(self, regrp, string, restr):
        msg = "`{}` argument value '{}' failed regex fullmatch '{}'".format(
            regrp, string, restr
        )
        super(Exception, self).__init__(msg)


RE_PATTERN_TYPE = type(re.compile(""))
RE_MATCH_TYPE = type(re.match("", ""))

def re_fullmatch_using_match(pattern, string, **kwargs):
    pattern_type = type(pattern)
    if pattern_type is str:
        pattern_str = pattern
    elif pattern_type is RE_PATTERN_TYPE:
        pattern_str = pattern.pattern
    else:
        raise TypeError("first argument must be string or compiled pattern")
    if not pattern_str.endswith('\Z'):
        if pattern is pattern_str:
            pattern += '\Z'
        else:
            pattern = re.compile(pattern_str+'\Z')
    return re.match(pattern, string, **kwargs)

try:
    RE_FULLMATCH_FN = re.fullmatch
except AttributeError:
    RE_FULLMATCH_FN = re_fullmatch_using_match


class Regex(object):
    recmp = None
    restr = None
    def __init__(self, string_or_match=None, re_function=RE_FULLMATCH_FN, **re_function_kwargs):
        string_or_match_type = type(string_or_match)
        if string_or_match is None:
            self.string = None
            self._populate_match(None)
        elif string_or_match_type is str:
            self.string = string_or_match
            self._re_function(re_function, in_place=True, **re_function_kwargs)
        elif string_or_match_type is RE_MATCH_TYPE:
            re_match = string_or_match
            self.string = re_match.string
            self._populate_match(re_match)
        else:
            raise cerr.InvalidArgumentError(
                "First argument to Regex class constructor can be None, "
                "a string to parse, or a `re` match object of type {} "
                "but was '{}' of type {}".format(RE_MATCH_TYPE, string_or_match, string_or_match_type))
    def _populate_match(self, re_match):
        if re_match is not None:
            self.matched = True
            self.re_match = re_match
            self.match_str = re_match.group(0)
            self.groupdict = re_match.groupdict()
        else:
            self._reset_match_attributes()
    def _reset_match_attributes(self):
        self.matched = False
        self.re_match = None
        self.match_str = None
        self.groupdict = None
    def _re_function(self, function, string=None, in_place=True, **kwargs):
        if string is not None:
            use_string = string
            if in_place:
                self.string = string
        elif self.string is not None:
            use_string = self.string
        else:
            raise cerr.InvalidArgumentError(
                "Argument `string` must be provided when calling `re` function "
                "on Regex object that has not been provided a search string prior"
            )
        match_results = function(self.restr if kwargs else self.recmp, use_string, **kwargs)
        if function is re.findall:
            return match_results
        elif function is re.finditer:
            return self._yield_match_results(match_results, in_place)
        else:
            re_match = match_results
            if in_place:
                result_obj = self
                result_obj._populate_match(re_match)
            else:
                result_obj = type(self)(string_or_match=re_match)
            return result_obj
    def _yield_match_results(self, match_results, in_place):
        for re_match in match_results:
            if in_place:
                result_obj = self
                result_obj._populate_match(re_match)
            else:
                result_obj = type(self)(string_or_match=re_match)
            yield result_obj
    def clear(self):
        self.string = None
        self._reset_match_attributes()
    def search(self, string=None, return_new=False, **kwargs):
        return self._re_function(re.search, string=string, in_place=(not return_new), **kwargs)
    def match(self, string=None, return_new=False, **kwargs):
        return self._re_function(re.match, string=string, in_place=(not return_new), **kwargs)
    def fullmatch(self, string=None, return_new=False, **kwargs):
        return self._re_function(RE_FULLMATCH_FN, string=string, in_place=(not return_new), **kwargs)
    def findall(self, string=None, return_new=False, **kwargs):
        return self._re_function(re.findall, string=string, in_place=(not return_new), **kwargs)
    def finditer(self, string=None, return_new=False, **kwargs):
        return self._re_function(re.finditer, string=string, in_place=(not return_new), **kwargs)
