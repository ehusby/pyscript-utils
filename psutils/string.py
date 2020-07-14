
def startswith_one_of_coll(check_string, string_starting_coll, case_sensitive=True, return_match=False):
    for s_start in string_starting_coll:
        if check_string.startswith(s_start) or (not case_sensitive and check_string.lower().startswith(s_start.lower())):
            return s_start if return_match else True
    return None if return_match else False

def starts_one_of_coll(string_starting, string_coll, case_sensitive=True, return_match=False):
    for s in string_coll:
        if s.startswith(string_starting) or (not case_sensitive and s.lower().startswith(string_starting.lower())):
            return s if return_match else True
    return None if return_match else False

def endswith_one_of_coll(check_string, string_ending_coll, case_sensitive=True, return_match=False):
    for s_end in string_ending_coll:
        if check_string.endswith(s_end) or (not case_sensitive and check_string.lower().endswith(s_end.lower())):
            return s_end if return_match else True
    return None if return_match else False

def ends_one_of_coll(string_ending, string_coll, case_sensitive=True, return_match=False):
    for s in string_coll:
        if s.endswith(string_ending) or (not case_sensitive and s.lower().endswith(string_ending.lower())):
            return s if return_match else True
    return None if return_match else False


def get_index_fmtstr(num_items, min_digits=3):
    return '{:0>'+str(max(min_digits, len(str(num_items))))+'}'
