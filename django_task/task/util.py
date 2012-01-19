""" Various utility methods for `taskweb` """


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
