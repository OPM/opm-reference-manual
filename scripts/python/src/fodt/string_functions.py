def parse_parts(range_string: str):
    parts = set()

    for element in range_string.split(','):
        int_lst = [int(x) for x in element.split('-')]
        if len(int_lst) == 1:
            parts.add(int_lst[0])
        else:
            for range_val in range(min(int_lst), max(int_lst) + 1):
                parts.add(range_val)

    return list(parts)
