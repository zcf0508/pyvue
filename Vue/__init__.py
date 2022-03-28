import sys
import threading
from Vue.Proxy import cleanup, effect, trigger, track
from Vue.utils import isoriginal

job_queue = set()
threads = []

is_flushing = False


def flush_job():
  global job_queue
  global threads
  global is_flushing

  if is_flushing:
    return
  is_flushing = True

  def finish():
    global is_flushing
    is_flushing = False

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
  finish()


def computed(getter):
  global value
  global dirty
  value = None
  dirty = True

  def scheduler_fn(fn):
    global dirty
    if not dirty:
      dirty = True
      trigger(obj, 'value')

  effect_fn = effect(getter, {'scheduler': scheduler_fn, 'lazy': True})

  def get_value():
    global value
    global dirty

    if dirty:
      value = effect_fn()
      dirty = False
    track(obj, 'value')
    return value

  class Cdict(object):

    def __init__(self, data=None):
      self._data = data

    @property
    def value(self):
      return get_value()

    def __getitem__(self, key):
      if key == 'value':
        return get_value()

  obj = Cdict()

  return obj


def watch(source, cb, options={}):

  getter = None

  def traverse(value, seen=set()):
    if isoriginal(value) or value is None or value in seen:
      return
    seen.add(value)

    if '_data' in value.__dict__:
      for k in value.__dict__['_data']:
        traverse(value[k], seen)
    else:
      for k in value.__dict__:
        traverse(value[k], seen)

    return value

  if hasattr(source, '__call__'):
    getter = source
  else:

    def fn():
      traverse(source)

    getter = fn

  def effect_lambda_fn():
    return getter()

  global old_value
  global new_value
  old_value = None
  new_value = None

  global cleanup
  cleanup = None

  def on_invalidate(fn):
    global cleanup
    cleanup = fn

  def job(fn=None):
    global old_value
    global new_value
    global cleanup
    new_value = effect_fn()
    if cleanup:
      cleanup()
    cb(new_value, old_value, on_invalidate)
    old_value = new_value

  def scheduler_fn(fn):
    if 'flush' in options and options['flush'] == 'post':
      global job_queue
      job_queue.add(job)
      threading.Thread(target=flush_job).start()
    else:
      job()

  effect_fn = effect(effect_lambda_fn, {"scheduler": scheduler_fn, 'lazy': True})

  if 'immediate' in options and options['immediate']:
    job()
  else:
    old_value = effect_fn()