def get_xp_for_next_level(level):
    if level < 3:
        return 10
    elif level < 7:
        return 15
    elif level < 10:
        return 20
    elif level < 15:
        return 25
    elif level < 18:
        return 30
    else:
        return 40


def get_level_thresholds(level):
    total = 0

    for lvl in range(level):
        total += get_xp_for_next_level(lvl)

    start = total
    end = total + get_xp_for_next_level(level)

    return start, end