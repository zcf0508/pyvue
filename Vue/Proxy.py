active_effect = None
effect_stack = []


def cleanup(effct_fn):
  for dep in effct_fn.deps:
    dep.pop()
  effct_fn.deps = []


def effect(fn, options={}):

  def effect_fn():
    cleanup(effect_fn)
    global active_effect
    active_effect = effect_fn
    global effect_stack
    effect_stack.append(effect_fn)
    res = fn()
    effect_stack.pop()
    active_effect = effect_stack[len(effect_stack) - 1] if len(effect_stack) > 0 else None
    return res

  effect_fn.options = options
  effect_fn.deps = []
  if 'lazy' not in options or ('lazy' in options and not options['lazy']):
    effect_fn()
  return effect_fn


bucket = dict()


def track(target, key):
  global bucket
  global active_effect
  if not active_effect:
    return
  deps_map = bucket.get(target)
  if not deps_map:
    deps_map = {}
    bucket[target] = deps_map
  deps = deps_map.get(key)
  if not deps:
    deps = set()
    deps_map[key] = deps
  deps.add(active_effect)
  active_effect.deps.append(deps)


def trigger(target, key):
  global active_effect
  global bucket
  deps_map = bucket.get(target)
  if not deps_map:
    return
  effects = deps_map.get(key)
  if effects:
    effect_to_run = set()

    for effect_fn in iter(effects):
      if effect_fn is not active_effect:
        effect_to_run.add(effect_fn)

    for effect_fn in iter(effect_to_run):
      if 'scheduler' in effect_fn.options and effect_fn.options['scheduler']:
        effect_fn.options['scheduler'](effect_fn)
      else:
        effect_fn()


class Proxy(object):

  def __init__(self, data):
    self._data = data

  def __getitem__(self, key):
    track(self, key)
    return self._data[key]

  def __setitem__(self, key, value):
    self._data[key] = value
    trigger(self, key)
