from operator import truediv
from typing import Generic, TypeVar

from Vue.utils import is_ref


T = TypeVar("T")


class ProxyRefs(Generic[T]):
    def __init__(self, o):
        self._data = o

    def __getitem__(self, key):
        value = self._data[key]
        return value.value if is_ref(value) else value

    def __setitem__(self, key, val):
        value = self._data[key]
        if is_ref(value):
            value.value = val
            return
        value = val


def proxy_refs(o: T) -> ProxyRefs[T]:
    return ProxyRefs(o)
