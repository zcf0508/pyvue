import sys
import threading
from typing import Callable, Generic, Set, TypeVar
from Vue.Proxy import Proxy, cleanup, effect, trigger, track
from Vue.utils import isoriginal

T = TypeVar("T")

job_queue: Set = set()  # 定义一个任务队列
threads = []

is_flushing = False  # 一个标志代表是否正在刷新队列


def flush_job():
    global job_queue
    global threads
    global is_flushing

    # 如果队列正在刷新，则什么都不做
    if is_flushing:
        return

    # 设置为 True 表示正在刷新
    is_flushing = True

    for job in iter(job_queue):

        def task(job):
            import time

            time.sleep(sys.float_info.min)
            job()

        t = threading.Thread(target=task(job))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    # 结束后重置 is_flushing
    is_flushing = False


global c_value  # 用来缓存上一次的计算结果
global c_dirty  # dirty 标志，用来标识是否需要重新计算值

c_value = None
c_dirty = True  # 为 True 则标识着「脏」，需要重新计算


def computed(getter):
    def scheduler_fn(fn):
        global c_dirty

        # 在调度器中将 dirty 重置为 True
        if not c_dirty:
            c_dirty = True

            # 当计算属性以来的响应式数据变化时，手动调用 trigger 函数出发响应
            trigger(obj, "value", "SET")

    effect_fn = effect(getter, {"scheduler": scheduler_fn, "lazy": True})

    def get_value():
        global c_value
        global c_dirty

        # 只有「脏」时才计算值，并将得到的结果缓存到 value 中
        if c_dirty:
            c_value = effect_fn()

            # 将 dirty 设置为 False ，下一次访问直接使用缓存的 value 中的值
            c_dirty = False

        # 当读取 value 属性时，手动调用 track 函数进行跟踪
        track(obj, "value")
        return c_value

    class Cdict(object):
        @property
        def value(self):
            # 当读取 value 时才执行 effect_fn
            return get_value()

        def __getitem__(self, key):
            # 当读取 value 时才执行 effect_fn
            if key == "value":
                return get_value()

    obj = Cdict()

    return obj


# 定义 getter
global w_getter
w_getter = None

# 定义旧值与新值
global w_old_value
global w_new_value
w_old_value = None
w_new_value = None

# cleanup 用来存储用户注册的过期回调
global w_cleanup
w_cleanup = None


def watch(source, cb: Callable, options={}):
    """
    watch 函数接受两个参数

    Args:
    source: 是响应式数据
    cb: 是回调函数
    """

    def traverse(value, seen=set()):
        # 如果要读取的数据是原始值，或者已经被读取过了，那么什么都不做
        # TODO: 这里设计 Python 的基础类型，需要进一步研究
        if isoriginal(value) or value is None or value in seen:
            return

        # 讲数据添加到 seen 中，代表遍历地读取过了，避免循环引起引用的死循环
        seen.add(value)

        if "_data" in value.__dict__:
            for k in value.__dict__["_data"]:
                traverse(value[k], seen)
        else:
            # TODO: 暂不考虑其它的数据结构
            # 读取对象的没一个值，并递归地调用 traverse 进行处理
            for k in value.__dict__:
                traverse(value[k], seen)

        return value

    global w_getter

    # 如果 source 是函数，说明用户传递的是 getter ，所以直接把 source 赋值给 getter
    if hasattr(source, "__call__"):
        w_getter = source
    else:

        def fn():
            # 调用 traverse 函数递归地读取
            traverse(source)

        w_getter = fn

    def effect_lambda_fn():
        return w_getter()

    # 定义旧值与新值
    global w_old_value
    global w_new_value

    global w_cleanup  # cleanup 用来存储用户注册的过期回调

    # 定义 on_invalidate 函数
    def on_invalidate(fn):
        global w_cleanup
        # 将过期回调存储到 cleanup 中
        w_cleanup = fn

    def job(fn=None):
        global w_old_value
        global w_new_value
        global w_cleanup

        # 在 scheduler 中重新执行副作用函数，得到的是新值
        w_new_value = effect_fn()

        # 在调用回调函数 cb 之前，先调用过期回调
        if w_cleanup:
            w_cleanup()

        # 将旧值与新值作为回调函数的参数，将 on_invalidate 作为第三个参数，以便用户使用
        cb(w_new_value, w_old_value, on_invalidate)

        # 更新旧值，不然下一次会得到错误的旧值
        w_old_value = w_new_value

    def scheduler_fn(fn):
        if "flush" in options and options["flush"] == "post":
            global job_queue

            # 每次调用时，讲副作用函数添加到 job_queue 队列中
            job_queue.add(job)

            threading.Thread(target=flush_job).start()
        else:
            job()

    effect_fn = effect(effect_lambda_fn, {"scheduler": scheduler_fn, "lazy": True})

    # 当 immediate 为 True 时立即执行 job， 从而触发回调执行
    if "immediate" in options and options["immediate"]:
        job()
    else:
        # 手动调用副作用函数，拿到的值就是旧值
        w_old_value = effect_fn()


def create_reactive(obj, is_shallow=False, is_readonly=False, parent=None):
    return Proxy(obj, is_shallow, is_readonly, parent)


def reactive(obj: T, parent=None) -> Proxy[T]:
    return create_reactive(obj, parent=parent)


def shallow_reactive(obj: T, parent=None) -> Proxy[T]:
    return create_reactive(obj, True, parent=parent)


def readonly(obj: T, parent=None) -> Proxy[T]:
    return create_reactive(obj, False, True, parent=parent)


def shallow_readonly(obj: T, parent=None) -> Proxy[T]:
    return create_reactive(obj, True, True, parent=parent)


def ref(val):
    return reactive({"_v_is_ref": True, "value": val})


def to_ref(obj, key):
    class ToRef:
        def __init__(self, o):
            self._v_is_ref = True
            self._data = o

        @property
        def value(self):
            return self._data[key]

        @value.setter
        def value(self, val):
            self._data[key] = val

    return ToRef(obj)


def to_refs(obj):
    ret = {}

    for key in obj.keys():
        ret.setdefault(key, to_ref(obj, key))

    return ret
