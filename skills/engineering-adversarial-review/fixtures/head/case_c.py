"""Synthetic head: only encoder changes; decoder defect persists."""


def decode_csv(value):
    if not value:
        return None
    return value.split(",")


def encode_csv(values):
    result = ""
    for index, value in enumerate(values):
        if index:
            result += ","
        result += value
    return result
