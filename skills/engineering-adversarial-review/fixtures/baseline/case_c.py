"""Synthetic baseline: pre-existing empty-input decoder defect."""


def decode_csv(value):
    if not value:
        return None
    return value.split(",")


def encode_csv(values):
    return ",".join(values)
