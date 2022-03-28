import sys, time
from Vue.Proxy import Proxy, effect
from Vue import computed, watch
import asyncio

import threading

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

  # print(job_queue)

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


data = {
    'foo': 1,
    'bar': 2,
}

obj = Proxy(data)


def effect1():
  return obj['foo'] + obj['bar']


def scheduler_fn(fn):
  global job_queue
  job_queue.add(fn)
  threading.Thread(target=flush_job).start()


effect_fn = effect(
    effect1,
    {
        # 'scheduler': scheduler_fn,
        'lazy': True
    })

# print(effect_fn())

# sum = computed(lambda: obj['foo']+obj['bar'])

# def effect2():
#   print(sum['value'])

# effect(effect2)

# obj['foo']+=1


def get_obj():
  return obj['foo']


global final_data

final_data = None


def watch_cb(new_value, old_value, on_invalidate):

  global expired
  expired = False

  def invalidate():

    global expired
    expired = True

  now = time.time()
  print(now)
  time.sleep(1)
  
  if not expired:
    global final_data
    final_data = now

  on_invalidate(invalidate)


watch(
    get_obj,
    watch_cb,
    {
        # 'immediate':True，
        # 'flush': 'post'
    })

obj['foo'] += 1
time.sleep(0.2)
obj['foo'] += 1

time.sleep(0.1)
print('final_data', final_data)
