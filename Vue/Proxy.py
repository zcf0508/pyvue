import binascii
import copy
import os
from typing import Dict, Generic, TypeVar
from enum import Enum
from warnings import warn

from Vue.utils import is_ref

active_effect = None  # 用一个全局变量存贮被注册的副作用函数
effect_stack = []  # effect 栈

ITERATE_KEY = binascii.hexlify(os.urandom(8)).decode("utf-8")
INDEX_KEY = binascii.hexlify(os.urandom(8)).decode("utf-8")

TriggerType = Enum("TriggerType", ("SET", "ADD", "DELETE"))


def cleanup(effect_fn):

    # 遍历 effect_fn.deps 数组
    for dep in effect_fn.deps:
        # 将 effect_fn 从依赖集合中移除
        try:
            dep.remove(effect_fn)
        except BaseException as e:
            # print(e)
            pass

    # 重置 effect_fn.deps 数组
    effect_fn.deps = []


def effect(fn, options={}):
    def effect_fn():
        global active_effect
        global effect_stack

        # 调用 cleanup 函数完成清除工作
        cleanup(effect_fn)

        # 当 effect_fn 执行时，将其设置为当前激活的副作用函数
        active_effect = effect_fn

        # 在调用副作用函数之前将当前副作用函数压入栈中
        effect_stack.append(effect_fn)

        # 将 fn 的执行结果存储到 res 中
        res = fn()

        # 在当前副作用函数执行完毕后，将当前副作用函数弹出栈
        effect_stack.pop()

        # 并把 active_effect 还原为之前的值
        active_effect = (
            effect_stack[len(effect_stack) - 1] if len(effect_stack) > 0 else None
        )

        # 将 res 作为 effect_fn 的返回值
        return res

    # 将 options 挂在到 effect_fn 上
    effect_fn.options = options

    # effect_fn.deps 用来存储所有与该副作用函数相关联的依赖集合
    effect_fn.deps = []

    # 只有在非 lazy 的时候，才执行
    if "lazy" not in options or ("lazy" in options and not options["lazy"]):
        effect_fn()  # 执行副作用函数

    # 将副作用函数作为返回值返回
    return effect_fn


bucket: Dict = dict()  # 存储副作用函数的桶


def track(target, key):
    # 没有 active_effect ，直接return
    if not active_effect:
        return

    # 根据 target 从桶中取得 deps_map   key-->effects
    deps_map = bucket.get(target)

    # 如果不存在 deps_map ，那么新建一个 map 并与 target 关联
    if not deps_map:
        deps_map = dict()
        bucket[target] = deps_map

    # 再根据 key 取得 deps ，它是一个 set 类型，里面存储着所有与当前 key 相关的副作用函数： effcts
    deps = deps_map.get(key)

    # 如果不存在 deps ，那么新建一个 set 并与 key 关联
    if not deps:
        deps = set()
        deps_map[key] = deps

    # 将当前激活的副作用函数添加到桶中
    deps.add(active_effect)

    # deps就是一个与当前副作用函数存在联系的依赖集合
    # 将其添加到 active_effect.deps 数组中
    active_effect.deps.append(deps)


def trigger(target, key, type):
    # 根据 target 从桶中取得 deps_map   key-->effects
    deps_map = bucket.get(target)
    if not deps_map:
        return

    # 根据 key 取得所有副作用函数 effects
    effects = deps_map.get(key)
    # 取得与 ITERATE_KEY 相关联的副作用函数
    iterate_effects = deps_map.get(ITERATE_KEY)
    # 取得与 INDEX_KEY 相关联的副作用函数
    index_effects = deps_map.get(INDEX_KEY)

    # 将 effects 转换为一个新的 set
    effect_to_run = set()
    if effects:
        for effect_fn in iter(effects):

            # 如果 trigger 触发执行的副作用函数与当前正在执行的副作用函数相同，则不执行触发
            if effect_fn is not active_effect:
                effect_to_run.add(effect_fn)

    if type == TriggerType.ADD or type == TriggerType.DELETE:
        # 将 ITERATE_KEY 相关联的副作用函数也添加到 effect_to_run
        if iterate_effects:
            for effect_fn in iter(iterate_effects):

                # 如果 trigger 触发执行的副作用函数与当前正在执行的副作用函数相同，则不执行触发
                if effect_fn is not active_effect:
                    effect_to_run.add(effect_fn)

    # 将 INDEX_KEY 相关联的副作用函数也添加到 effect_to_run
    if index_effects:
        for effect_fn in iter(index_effects):

            # 如果 trigger 触发执行的副作用函数与当前正在执行的副作用函数相同，则不执行触发
            if effect_fn is not active_effect:
                effect_to_run.add(effect_fn)

    for effect_fn in iter(effect_to_run):
        # 如果一个副作用函数存在调度器，则调用该调度器，并将副作用函数作为参数传递
        if "scheduler" in effect_fn.options and effect_fn.options["scheduler"]:
            effect_fn.options["scheduler"](effect_fn)
        else:
            # 否则直接执行副作用函数
            effect_fn()


T = TypeVar("T")


class Proxy(Generic[T]):
    def __init__(self, data: T, is_shallow=False, is_readonly=False, parent=None):
        self._data = data
        self._is_iter_ = hasattr(data, "__iter__")
        self._is_shallow = is_shallow
        self._is_readonly = is_readonly
        self._parent = parent

    @staticmethod
    def raw(target):
        if isinstance(target, Proxy):
            res = target._data
        else:
            res = target

        if isinstance(res, dict):
            for key in res:
                res[key] = Proxy.raw(res[key])

        if isinstance(res, list) or isinstance(res, set):
            for index, val in enumerate(res):
                res[index] = Proxy.raw(res[index])

        return res

    def _auto_track(self, target, key):
        try:
            if self._parent:
                if isinstance(self._parent._data, dict):
                    for p_key, p_val in self._parent.items():
                        if Proxy.is_equal(p_val, target):
                            track(self._parent, p_key)
                elif isinstance(self._parent._data, list) or isinstance(
                    self._parent._data, set
                ):
                    for p_index, p_val in enumerate(self._parent):
                        if Proxy.is_equal(p_val, target):
                            track(self._parent, p_index)
            else:
                track(target, key)
        except BaseException as e:
            track(target, key)

    def _auto_trigger(self, target, key, type):
        try:
            if self._parent:
                if isinstance(self._parent._data, dict):
                    for p_key, p_val in self._parent.items():
                        if Proxy.is_equal(p_val, target):
                            trigger(self._parent, p_key, TriggerType.SET)
                elif isinstance(self._parent._data, list) or isinstance(
                    self._parent._data, set
                ):
                    for p_index, p_val in enumerate(self._parent):
                        if Proxy.is_equal(p_val, target):
                            trigger(self._parent, p_index, TriggerType.SET)
            else:
                trigger(target, key, type)
        except BaseException as e:
            trigger(target, key, type)

    def __str__(self) -> str:
        return "Proxy " + str(self._data)

    __repr__ = __str__

    @staticmethod
    def is_equal(obj_a, obj_b):

        return (obj_a._data if isinstance(obj_a, Proxy) else obj_a) == (
            obj_b._data if isinstance(obj_b, Proxy) else obj_b
        )

    def __getitem__(self, key=-1):
        if isinstance(key, int) and key < 0:
            key = len(self._data) + key

        if isinstance(self._data, list):
            if key > len(self._data) or key < 0:
                raise IndexError("list index out of range")
        res = self._data[key]
        if self._is_shallow:
            return res

        # 非只读的时候才需要建立响应联系
        if not self._is_readonly:
            self._auto_track(self, key)

        if res != None and (
            isinstance(res, dict) or isinstance(res, list) or isinstance(res, set)
        ):

            from Vue import reactive, readonly

            self._data[key] = (
                readonly(res, self) if self._is_readonly else reactive(res, self)
            )
            return self._data[key]

        return res.value if is_ref(res) else res  # 返回属性值

    def __setitem__(self, key, new_value):
        if self._is_readonly:
            warn(f"{key} is readonly")
            return
        value = self._data[key]
        old_value = self._data[key]

        if is_ref(value):
            value.value = new_value
        else:
            self._data[key] = new_value  # 设置属性值

        # 比较新值与旧值，增加类型判断避免bool值与int值相等的问题
        if old_value != new_value or type(old_value) != type(new_value):
            self._auto_trigger(self, key, TriggerType.SET)

    def __iter__(self):
        if self._is_iter_:
            self._auto_track(self, ITERATE_KEY)
            return self._data.__iter__()
        else:
            raise Exception("Not iterable")

    def __next__(self):
        if self._is_iter_ and hasattr(self._data, "__next__"):
            self._auto_track(self, ITERATE_KEY)
            return self._data.__next__()
        else:
            raise Exception("Not iterable")

    def __len__(self):
        self._auto_track(self, ITERATE_KEY)
        return len(self._data)

    def clear(self):
        if self._is_readonly:
            warn("This is readonly")
            return
        if isinstance(self._data, dict):
            for key in self._data:
                del self._data[key]
                self._auto_trigger(self, key, TriggerType.DELETE)
        elif isinstance(self._data, list):
            for index, item in enumerate(self._data[:]):
                del self._data[index]
                self._auto_trigger(self, index, TriggerType.DELETE)

    def copy(self):
        from Vue import reactive, readonly

        obj = (
            readonly(self._data, self)
            if self._is_readonly
            else reactive(self._data, self)
        )

        return obj

    def shallow_copy(self):
        from Vue import shallow_reactive, shallow_readonly

        obj = (
            shallow_readonly(self._data, self)
            if self._is_readonly
            else shallow_reactive(self._data, self)
        )

        return obj

    def deepcopy(self):
        from Vue import reactive, readonly

        obj = (
            readonly(self._data, None)
            if self._is_readonly
            else reactive(self._data, None)
        )

        return obj

    def shallow_deepcopy(self):
        from Vue import shallow_reactive, shallow_readonly

        obj = (
            shallow_readonly(self._data, None)
            if self._is_readonly
            else shallow_reactive(self._data, None)
        )

        return obj

    def __delitem__(self, key):
        if key in self._data:
            if self._is_readonly:
                warn(f"{key} is readonly")
                return
            del self._data[key]
            self._auto_trigger(self, key, TriggerType.DELETE)
        else:
            raise KeyError

    def pop(self, key=-1, default=None):
        if self._is_readonly:
            warn("This is readonly")
            return

        if isinstance(self._data, set):
            old_value = copy.deepcopy(self._data)
            res = self._data.pop()
            for index, item in enumerate(old_value):
                if item == res:
                    self._auto_trigger(self, index, TriggerType.DELETE)
                    break
            return res

        if isinstance(self._data, list) and isinstance(key, int) and key < 0:
            key = len(self._data) + key

        if isinstance(self._data, dict):
            has_key = hasattr(self._data, key)
            res = self._data.pop(key, default)
            if has_key:
                self._auto_trigger(self, key, TriggerType.DELETE)
        elif isinstance(self._data, list):
            if key > len(self._data) or key < 0:
                raise IndexError("list index out of range")
            res = self._data.pop(key)
            self._auto_trigger(self, key, TriggerType.DELETE)
        return res

    def remove(self, obj):
        index = -1
        for i, item in enumerate(self._data):
            if item == obj:
                index = i

        if index >= 0:
            if self._is_readonly:
                warn("This is readonly")
                return
            self._data.remove(obj)
            self._auto_trigger(self, index, TriggerType.DELETE)
        else:
            if isinstance(self._data, list):
                raise ValueError(f"{obj} not in list")
            if isinstance(self._data, set):
                raise KeyError(f"{obj} not in set")

    def update(self, obj):
        if isinstance(self._data, set):
            old_length = len(self._data)
            will_add = False
            for item in obj:
                if item not in self._data:
                    will_add = True
            if will_add:
                if self._is_readonly:
                    warn("This is readonly")
                    return
                self._data.update(obj)
                if old_length < len(self._data):
                    self._auto_trigger(self, len(self._data), TriggerType.ADD)
        elif isinstance(self._data, dict):
            for key, value in obj.items():
                if key in self._data:
                    if value != self._data[key] or type(value) != type(self._data[key]):
                        if self._is_readonly:
                            warn("This is readonly")
                            return
                        self._data[key] = value
                        self._auto_trigger(self, key, TriggerType.SET)
                else:
                    self.setdefault(key, value)

    # dict 方法

    def get(self, key, default):
        try:
            res = self._data[key]
            self._auto_track(self, key)
            return res
        except KeyError:
            return default

    def items(self):
        if self._is_iter_:
            self._auto_track(self, ITERATE_KEY)
            return self._data.items()
        else:
            raise Exception("Not iterable")

    def keys(self):
        if self._is_iter_:
            self._auto_track(self, ITERATE_KEY)
            return self._data.keys()
        else:
            raise Exception("Not iterable")

    def popitem(self):
        if self._is_readonly:
            warn("This is readonly")
            return
        key = list(self._data.keys())[-1]
        del self._data[key]
        self._auto_trigger(self, key, TriggerType.DELETE)

    def setdefault(self, key, default=None):
        if key not in self._data.keys():
            if self._is_readonly:
                warn("This is readonly")
                return
            res = self._data.setdefault(key, default)

            if self._is_shallow:
                return res

            self._auto_trigger(self, key, TriggerType.ADD)

            if res != None and (
                isinstance(default, dict)
                or isinstance(default, list)
                or isinstance(default, set)
            ):
                from Vue import reactive

                return reactive(res, self)
            return res
        else:
            if default != self._data[key]:
                if self._is_readonly:
                    warn("This is readonly")
                    return
                self._data[key] = default

                if self._is_shallow:
                    return default

                self._auto_trigger(self, key, TriggerType.SET)

                if default != None and (
                    isinstance(default, dict)
                    or isinstance(default, list)
                    or isinstance(default, set)
                ):
                    from Vue import reactive

                    return reactive(default, self)
                return default

    def values(self):
        if self._is_iter_:
            self._auto_track(self, ITERATE_KEY)
            return self._data.values()
        else:
            raise Exception("Not iterable")

    # list 方法

    def append(self, value):
        if self._is_readonly:
            warn("This is readonly")
            return
        self._data.append(value)
        self._auto_trigger(self, len(self._data) - 1, TriggerType.ADD)

    def count(self, obj):
        num = 0
        for index, item in enumerate(self._data):
            if item == obj:
                self._auto_track(self, index)
                num += 1
        self._auto_track(self, ITERATE_KEY)
        return num

    def extend(self, list):
        if self._is_readonly:
            warn("This is readonly")
            return
        olg_lenth = len(self._data)
        self._data.extend(list)
        for index in range(olg_lenth, len(self._data)):
            self._auto_trigger(self, index, TriggerType.ADD)

    def index(self, key, start=None, end=None):
        try:
            res = self._data.index(key, start or 0, end or len(self._data))
            self._auto_track(self, INDEX_KEY)
            return res
        except ValueError:
            raise ValueError(f"{key} is not in list")

    def insert(self, index, obj):
        if self._is_readonly:
            warn("This is readonly")
            return
        self._data.insert(index, obj)
        self._auto_trigger(self, index, TriggerType.ADD)

    def reverse(self):
        if self._is_readonly:
            warn("This is readonly")
            return
        old_value = self._data[:]
        self._data.reverse()
        for index, (old_item, new_item) in enumerate(zip(old_value, self._data)):
            if old_item != new_item or type(old_item) != type(new_item):
                self._auto_trigger(self, index, TriggerType.SET)

    def sort(self, key=None, reverse=False):
        if self._is_readonly:
            warn("This is readonly")
            return
        if key and reverse:
            raise TypeError("sort() takes no positional arguments")
        old_value = self._data[:]

        if key:
            self._data.sort(key=key)
        elif reverse:
            self._data.sort(reverse=reverse)

        for index, (old_item, new_item) in enumerate(zip(old_value, self._data)):
            if old_item != new_item or type(old_item) != type(new_item):
                self._auto_trigger(self, index, TriggerType.SET)

    # set 方法

    def add(self, elmnt):
        if self._is_readonly:
            warn("This is readonly")
            return
        old_length = len(self._data)
        self._data.add(elmnt)
        if len(self._data) > old_length:
            self._auto_trigger(self, len(self._data) - 1, TriggerType.ADD)

    def difference_update(self, set_obj):
        if self._is_readonly:
            warn("This is readonly")
            return
        old_value = copy.deepcopy(self._data)
        self._data.difference_update(set_obj)
        for index, item in enumerate(old_value):
            if item not in self._data:
                self._auto_trigger(self, index, TriggerType.DELETE)

    def difference(self, set_obj):
        res = self._data.difference(set_obj)
        return res

    def discard(self, value):
        index = -1
        for i, item in enumerate(self._data):
            if item == value:
                index = i
        if index >= 0:
            if self._is_readonly:
                warn("This is readonly")
                return
            self._data.discard(value)
            self._auto_trigger(self, index, TriggerType.DELETE)

    def intersection(self, set_obj, *args):
        if args:
            res = self._data.intersection(set_obj, *args)
        else:
            res = self._data.intersection(set_obj)
        return res

    def intersection_update(self, set_obj, *args):
        if self._is_readonly:
            warn("This is readonly")
            return
        old_value = copy.deepcopy(self._data)
        if args:
            self._data.intersection_update(set_obj, *args)
        else:
            self._data.intersection_update(set_obj)
        for index, item in enumerate(old_value):
            if item not in self._data:
                self._auto_trigger(self, index, TriggerType.DELETE)

    def isdisjoint(self, set_obj):
        res = False
        for index, item in enumerate(self._data):
            if item in set_obj:
                self._auto_track(self, index)
                res = True
                break
        return res

    def issubset(self, set_obj):
        res = True
        for index, item in enumerate(self._data):
            if item not in set_obj:
                self._auto_track(self, index)
                res = False
                break
        return res

    def issuperset(self, set_obj):
        res = True
        for set_item in set_obj:
            if set_item not in self._data:
                for index, item in enumerate(self._data):
                    self._auto_track(self, index)
                res = True
                break
        return res

    def symmetric_difference(self, set_obj):
        res = self._data.symmetric_difference(set_obj)
        return res

    def symmetric_difference_update(self, set_obj: set):
        if self._is_readonly:
            warn("This is readonly")
            return
        set_obj_tmp = copy.deepcopy(set_obj)
        for new_item in copy.deepcopy(set_obj_tmp):
            if (
                isinstance(self._data, dict)
                or isinstance(self._data, list)
                or isinstance(self._data, set)
            ) and new_item not in self._data:
                self.add(new_item)
                set_obj_tmp.discard(new_item)

        for new_item in set_obj_tmp:
            if (
                isinstance(self._data, dict)
                or isinstance(self._data, list)
                or isinstance(self._data, set)
            ) and new_item in self._data:
                self.discard(new_item)

        return self._data

    def union(self, set_obj, *args):
        if args:
            res = self._data.union(set_obj, *args)
        else:
            res = self._data.union(set_obj)

        return res
