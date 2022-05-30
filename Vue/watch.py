import sys
import threading
from typing import Callable, Set
from .reactivity.Proxy import effect

from .utils import isoriginal

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
