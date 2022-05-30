from typing import TypeVar

from .Proxy import Proxy


T = TypeVar("T")


def _create_reactive(obj, is_shallow=False, is_readonly=False, parent=None):
    return Proxy(obj, is_shallow, is_readonly, parent)


def reactive(obj: T, parent=None) -> Proxy[T]:
    return _create_reactive(obj, parent=parent)


def shallow_reactive(obj: T, parent=None) -> Proxy[T]:
    return _create_reactive(obj, True, parent=parent)


def readonly(obj: T, parent=None) -> Proxy[T]:
    return _create_reactive(obj, False, True, parent=parent)


def shallow_readonly(obj: T, parent=None) -> Proxy[T]:
    return _create_reactive(obj, True, True, parent=parent)


def ref(val):
    return reactive({"_v_is_ref": True, "value": val})


class ToRef:
    def __init__(self, o, key):
        self._v_is_ref = True
        self._data = o
        self._key = key

    @property
    def value(self):
        return self._data[self._key]

    @value.setter
    def value(self, val):
        self._data[self._key] = val


def to_ref(obj, key):
    return ToRef(obj, key)


def to_refs(obj):
    ret = {}

    for key in obj.keys():
        ret.setdefault(key, to_ref(obj, key))

    return ret
