import binascii
import os
from typing import Dict
from enum import Enum
from warnings import warn

active_effect = None  # 用一个全局变量存贮被注册的副作用函数
effect_stack = []  # effect 栈

ITERATE_KEY = binascii.hexlify(os.urandom(8)).decode("utf-8")
INDEX_KEY = binascii.hexlify(os.urandom(8)).decode("utf-8")

TriggerType = Enum("TriggerType", ("SET", "ADD", "DELETE"))


def cleanup(effect_fn):

    # 遍历 effect_fn.deps 数组
    for dep in effect_fn.deps:
        # 将 effect_fn 从依赖集合中移除
        dep.remove(effect_fn)

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


class Proxy(object):
    def __init__(self, data, is_shallow=False, is_readonly=False):
        self._data = data
        self._is_iter_ = hasattr(data, "__iter__")
        self._is_shallow = is_shallow
        self._is_readonly = is_readonly

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
            track(self, key)

        if res != None and isinstance(res, dict):

            from Vue import reactive, readonly

            self._data[key] = readonly(res) if self._is_readonly else reactive(res)
            return self._data[key]

        return res  # 返回属性值

    def __setitem__(self, key, new_value):
        if self._is_readonly:
            warn(f"{key} is readonly")
            return
        old_value = self._data[key]
        self._data[key] = new_value  # 设置属性值

        # 比较新值与旧值，增加类型判断避免bool值与int值相等的问题
        if old_value != new_value or type(old_value) != type(new_value):
            trigger(self, key, TriggerType.SET)

    def __iter__(self):
        if self._is_iter_:
            track(self, ITERATE_KEY)
            return self._data.__iter__()
        else:
            raise Exception("Not iterable")

    def __next__(self):
        if self._is_iter_ and hasattr(self._data, "__next__"):
            track(self, ITERATE_KEY)
            return self._data.__next__()
        else:
            raise Exception("Not iterable")

    def items(self):
        if self._is_iter_:
            track(self, ITERATE_KEY)
            for key in self._data.keys():
                track(self, key)
            return self._data.items()
        else:
            raise Exception("Not iterable")

    def keys(self):
        if self._is_iter_:
            track(self, ITERATE_KEY)
            return self._data.keys()
        else:
            raise Exception("Not iterable")

    def values(self):
        if self._is_iter_:
            track(self, ITERATE_KEY)
            for key in self._data.keys():
                track(self, key)
            return self._data.values()
        else:
            raise Exception("Not iterable")

    def get(self, key, default):
        try:
            res = self._data[key]
            track(self, key)
            return res
        except KeyError:
            return default

    def setdefault(self, key, default):
        try:
            return self._data[key]
        except KeyError:
            res = self._data.setdefault(key, default)

            if self._is_shallow:
                return res

            trigger(self, key, TriggerType.ADD)

            if res != None and isinstance(res, dict):
                from Vue import reactive

                self._data[key] = reactive(res)
                return self._data[key]
            return res

    def __delitem__(self, key):
        if hasattr(self._data, key):
            if self._is_readonly:
                warn(f"{key} is readonly")
                return
            del self._data[key]
            trigger(self, key, TriggerType.DELETE)
        else:
            raise KeyError

    def pop(self, key=-1, default=None):
        if isinstance(key, int) and key < 0:
            key = len(self._data) + key
        if self._is_readonly:
            warn("This is readonly")
            return
        if isinstance(self._data, dict):
            has_key = hasattr(self._data, key)
            res = self._data.pop(key, default)
            if has_key:
                trigger(self, key, TriggerType.DELETE)
        elif isinstance(self._data, list):
            if key > len(self._data) or key < 0:
                raise IndexError("list index out of range")
            res = self._data.pop(key)
            trigger(self, key, TriggerType.DELETE)
        return res

    def clear(self):
        if self._is_readonly:
            warn("This is readonly")
            return
        if isinstance(self._data, dict):
            for key in self._data:
                del self._data[key]
                trigger(self, key, TriggerType.DELETE)
        elif isinstance(self._data, list):
            for index, item in enumerate(self._data[:]):
                del self._data[index]
                trigger(self, index, TriggerType.DELETE)

    def update(self, obj):
        for key, value in obj.items():
            if key in self._data:
                if value != self._data[key]:
                    trigger(self, key, TriggerType.SET)
                    self._data[key] = value
            else:
                self.setdefault(key, value)

    def popitem(self):
        key = list(self._data.keys())[-1]
        del self._data[key]
        trigger(self, key, TriggerType.DELETE)

    def __len__(self):
        track(self, ITERATE_KEY)
        return len(self._data)

    # list 方法

    def append(self, value):
        res = self._data.append(value)
        trigger(self, len(self._data) - 1, TriggerType.ADD)
        return res

    def count(self, key):
        num = 0
        for index, item in enumerate(self._data):
            if item == key:
                num += 1
        track(self, ITERATE_KEY)
        return num

    def extend(self, list):
        self._data.extend(list)
        trigger(self, len(self._data) - 1, TriggerType.ADD)
        return self._data

    def index(self, key):
        try:
            res = self._data.index(key)
            track(self, INDEX_KEY)
            return res
        except ValueError:
            raise ValueError(f"{key} is not in list")

    def insert(self, index, obj):
        self._data.insert(index, obj)
        trigger(self, index, TriggerType.ADD)
        return self._data

    def remove(self, obj):
        try:
            index = 0
            for i, item in enumerate(self._data):
                if item == obj:
                    index = i
            res = self._data.remove(obj)
            trigger(self, index, TriggerType.DELETE)
            return res
        except ValueError:
            raise ValueError(f"{obj} not in list")

    def reverse(self):
        old_value = self._data[:]
        self._data.reverse()
        for index, (old_item, new_item) in enumerate(zip(old_value, self._data)):
            if old_item != new_item or type(old_item) != type(new_item):
                trigger(self, index, TriggerType.SET)
        return self._data

    def sort(self, key=None, reverse=False):
        old_value = self._data[:]
        self._data.sort(key, reverse)
        for index, (old_item, new_item) in enumerate(zip(old_value, self._data)):
            if old_item != new_item or type(old_item) != type(new_item):
                trigger(self, index, TriggerType.SET)
        return self._data

    def copy(self):
        from Vue import reactive, readonly, shallow_reactive, shallow_readonly

        obj = (
            (readonly(self._data) if self._is_readonly else reactive(self._data))
            if not self._is_shallow
            else (
                shallow_readonly(self._data)
                if self._is_readonly
                else shallow_reactive(self._data)
            )
        )

        return obj
