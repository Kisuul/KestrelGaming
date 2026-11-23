"""Synthetic baseline: symmetric case normalization."""


class NameStore:
    def __init__(self):
        self._items = {}

    def put(self, key, value):
        self._items[key.casefold()] = value

    def get(self, key):
        return self._items.get(key.casefold())
