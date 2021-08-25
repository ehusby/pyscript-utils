
import operator

import psutils.custom_errors as cerr


class VersionString(object):
    def __init__(self, version, nelements=None, allow_alpha=False):
        self.is_numeric = (not allow_alpha)
        if type(version) in (list, tuple):
            nums_input = version
            nums_internal = []
            for n in nums_input:
                if type(n) is float:
                    n_float = n
                    n_int = int(n)
                    if n_float != n_int:
                        raise cerr.InvalidArgumentError(
                            "Non-integer element '{}' in version number list: {}".format(n, nums_input)
                        )
                    n = n_int
                if self.is_numeric:
                    try:
                        n = int(n)
                    except ValueError:
                        raise cerr.InvalidArgumentError(
                            "Non-numeric element '{}' in version number list: {}".format(n, nums_input)
                        )
                else:
                    n = str(n).strip()
                    if '.' in n:
                        raise cerr.InvalidArgumentError(
                            "Invalid element '{}' in version number list: {}".format(n, nums_input)
                        )
                nums_internal.append(n)
            self.nums = nums_internal
            self.string = '.'.join([str(n) for n in self.nums])
        else:
            version_string = version
            self.string = str(version_string).strip()
            if not self.is_numeric:
                self.nums = [n.strip() for n in self.string.split('.')]
            else:
                nums_internal = []
                for n in self.string.split('.'):
                    try:
                        n = int(n)
                    except ValueError:
                        raise cerr.InvalidArgumentError(
                            "Non-numeric element '{}' in version string: '{}'".format(n, version_string)
                        )
                    nums_internal.append(n)
                self.nums = nums_internal
        if nelements is not None:
            numel_diff = nelements - len(self.nums)
            if numel_diff < 0:
                raise cerr.InvalidArgumentError(
                    "Provided version string '{}' has more elements ({}) than `nelements` ({})".format(
                        self.string, len(self.nums), nelements
                    )
                )
            elif numel_diff > 0:
                self.nums.extend([0 if self.is_numeric else '0'] * numel_diff)
                self.string = '.'.join([str(n) for n in self.nums])
    def __str__(self):
        return self.string
    def __repr__(self):
        return self.string
    def _get_comparable_nums(self, other):
        if self.is_numeric and other.is_numeric:
            zero_num = 0
            this_nums = list(self.nums)
            other_nums = list(other.nums)
        else:
            zero_num = '0'
            this_nums = [str(n) for n in self.nums] if self.is_numeric else list(self.nums)
            other_nums = [str(n) for n in other.nums] if other.is_numeric else list(other.nums)
        numel_diff = len(other_nums) - len(this_nums)
        if numel_diff > 0:
            this_nums.extend([zero_num] * numel_diff)
        elif numel_diff < 0:
            other_nums.extend([zero_num] * (-numel_diff))
        if type(zero_num) is str:
            for i in range(len(this_nums)):
                ellen_diff = len(other_nums[i]) - len(this_nums[i])
                if ellen_diff > 0:
                    this_nums[i] = zero_num*ellen_diff + this_nums[i]
                elif ellen_diff < 0:
                    other_nums[i] = zero_num*(-ellen_diff) + other_nums[i]
        return this_nums, other_nums
    def _compare_absolute(self, other, inequality=False):
        this_nums, other_nums = self._get_comparable_nums(other)
        for i in range(len(this_nums)):
            if this_nums[i] != other_nums[i]:
                return inequality
        return (not inequality)
    def _compare_relative(self, other, op, allow_equal=False):
        this_nums, other_nums = self._get_comparable_nums(other)
        for i in range(len(this_nums)):
            if this_nums[i] != other_nums[i]:
                return op(this_nums[i], other_nums[i])
        return allow_equal
    def __eq__(self, other):
        return self._compare_absolute(other, inequality=False)
    def __ne__(self, other):
        return self._compare_absolute(other, inequality=True)
    def __gt__(self, other):
        return self._compare_relative(other, operator.gt, allow_equal=False)
    def __ge__(self, other):
        return self._compare_relative(other, operator.gt, allow_equal=True)
    def __lt__(self, other):
        return self._compare_relative(other, operator.lt, allow_equal=False)
    def __le__(self, other):
        return self._compare_relative(other, operator.le, allow_equal=True)
