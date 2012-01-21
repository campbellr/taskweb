""" Various utility methods for `taskweb` """
import re


# Borrowed from `taskw` (http://github.com/ralphbean/taskw)
def parse_line(line):
    """ Parse a single record (task) from a task database file.

    I don't understand why they don't just use JSON or YAML.  But that's okay.

    >>> parse_line('[description:"Make a python API for taskwarrior"]')
    {'description': 'Make a python API for taskwarrior'}

    """
    d = {}
    for key, value in re.findall(r'(\w+):"(.*?)"', line):
        d[key] = value

    return d


def parse_undo(data):
    """ Return a list of dictionaries representing the passed in
        `taskwarrior` undo data.
    """
    undo_list = []
    for segment in data.split('---'):
        parsed = {}
        undo = [line for line in segment.splitlines() if line.strip()]
        if not undo:
            continue

        parsed['time'] = undo[0].split(' ', 1)[1]
        if undo[1].startswith('old'):
            parsed['old'] = undo[1].split(' ', 1)[1]
            parsed['new'] = undo[2].split(' ', 1)[1]
        else:
            parsed['new'] = undo[1].split(' ', 1)[1]

        undo_list.append(parsed)

    return undo_list
