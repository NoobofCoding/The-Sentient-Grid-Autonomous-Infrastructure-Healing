MAX_LOAD_REDUCTION = 0.30
MIN_FREQUENCY = 49.5
MAX_FREQUENCY = 50.5


def cap_load_reduction(percent):
    return min(percent, MAX_LOAD_REDUCTION)