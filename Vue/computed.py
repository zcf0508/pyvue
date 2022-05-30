from .reactivity.Proxy import effect, track, trigger


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
