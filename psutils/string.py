
import textwrap


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


def wrap_multiline_str(text, width=float('inf')):
    """Format a multiline string, preserving indicated line breaks.

    Wraps the `text` (a string) so every line is at most `width` characters long.
    Common leading whitespace from every line in `text` is removed.
    Literal '\n' are considered line breaks, and area treated as such in wrapping.

    Args:
        text (str): A multiline string to be wrapped.

    Returns:
        str: The wrapped string.

    Example:
        animal_a = "Cats"
        animal_b = "Dogs"
        text = wrap_multiline_rfstr(
            rf\"""
            Cats and dogs are the most popular pets in the world.
            \n  1) {animal_a} are more independent and are generally
            cheaper and less demanding pets.
            \n  2) {animal_b} are loyal and obedient but require more
            attention and exercise, including regular walks.
            \""", width=40
        )
        >>> print(text)
        Cats and dogs are the most popular pets
        in the world.
          1) Cats are more independent and are
        generally cheaper and less demanding
        pets.
          2) Dogs are loyal and obedient but
        require more attention and exercise,
        including regular walks.
    """
    s_in = textwrap.dedent(text.strip('\n'))

    p_in = [p for p in s_in.split(r'\n')]
    p_out = [textwrap.fill(p, width=width) for p in p_in]

    return '\n'.join(p_out)


def get_index_fmtstr(num_items, min_digits=3):
    return '{:0>'+str(max(min_digits, len(str(num_items))))+'}'
