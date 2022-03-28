active_effect = None  # 用一个全局变量存贮被注册的副作用函数
effect_stack = [] # effect 栈


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
    active_effect = effect_stack[len(effect_stack) - 1] if len(effect_stack) > 0 else None
    
    # 将 res 作为 effect_fn 的返回值
    return res

  # 将 options 挂在到 effect_fn 上
  effect_fn.options = options

  # effect_fn.deps 用来存储所有与该副作用函数相关联的依赖集合
  effect_fn.deps = []

  # 只有在非 lazy 的时候，才执行
  if 'lazy' not in options or ('lazy' in options and not options['lazy']):
    effect_fn()  # 执行副作用函数
  
  # 将副作用函数作为返回值返回
  return effect_fn


bucket = dict()  # 存储副作用函数的桶


def track(target, key):
  global bucket
  global active_effect

  # 没有 active_effect ，直接return
  if not active_effect: return

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


def trigger(target, key):
  global active_effect
  global bucket

  # 根据 target 从桶中取得 deps_map   key-->effects
  deps_map = bucket.get(target)
  if not deps_map: return

  # 根据 key 取得所有副作用函数 effects
  effects = deps_map.get(key)
  if effects:
    # 将 effects 转换为一个新的 set
    effect_to_run = set()
    for effect_fn in iter(effects):

      # 如果 trigger 触发执行的副作用函数与当前正在执行的副作用函数相同，则不执行触发
      if effect_fn is not active_effect:
        effect_to_run.add(effect_fn)

    for effect_fn in iter(effect_to_run):
      # 如果一个副作用函数存在调度器，则调用该调度器，并将副作用函数作为参数传递
      if 'scheduler' in effect_fn.options and effect_fn.options['scheduler']:
        effect_fn.options['scheduler'](effect_fn)
      else:
        # 否则直接执行副作用函数
        effect_fn()


class Proxy(object):

  def __init__(self, data):
    self._data = data

  def __getitem__(self, key):
    track(self, key)
    return self._data[key]  # 返回属性值

  def __setitem__(self, key, value):
    self._data[key] = value  # 设置属性值
    trigger(self, key)
