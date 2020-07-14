
import operator


class VersionString(object):
    def __init__(self, ver_str_or_num):
        self.ver_str = str(ver_str_or_num)
        self.ver_num_list = [int(n) for n in self.ver_str.split('.')]
    def get_comparable_lists(self, other):
        this_list = list(self.ver_num_list)
        other_list = list(other.ver_num_list)
        if len(this_list) < len(other_list):
            this_list.extend([0]*(len(other_list)-len(this_list)))
        elif len(this_list) > len(other_list):
            other_list.extend([0]*(len(this_list)-len(other_list)))
        return this_list, other_list
    def __str__(self):
        return self.ver_str
    def __repr__(self):
        return self.ver_str
    def __compare_absolute(self, other, inequality=False):
        this_ver_num_list, other_ver_num_list = self.get_comparable_lists(other)
        for i in range(len(this_ver_num_list)):
            if this_ver_num_list[i] != other_ver_num_list[i]:
                return inequality
        return (not inequality)
    def __compare_relative(self, other, op, allow_equal=False):
        this_ver_num_list, other_ver_num_list = self.get_comparable_lists(other)
        for i in range(len(this_ver_num_list)):
            if this_ver_num_list[i] != other_ver_num_list[i]:
                return op(this_ver_num_list[i], other_ver_num_list[i])
        return allow_equal
    def __eq__(self, other):
        return self.__compare_absolute(other, inequality=False)
    def __ne__(self, other):
        return self.__compare_absolute(other, inequality=True)
    def __gt__(self, other):
        return self.__compare_relative(other, operator.gt, allow_equal=False)
    def __ge__(self, other):
        return self.__compare_relative(other, operator.gt, allow_equal=True)
    def __lt__(self, other):
        return self.__compare_relative(other, operator.lt, allow_equal=False)
    def __le__(self, other):
        return self.__compare_relative(other, operator.le, allow_equal=True)
