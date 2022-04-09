#!/usr/bin/python3

import sys
import threading
import time
from Vue.Proxy import Proxy, effect
from Vue import computed, watch


def test1():
  print('--test1--')

  data = {'text': 'hello world'}

  obj = Proxy(data)

  def effect_lambda():
    print(obj['text'])

  effect(effect_lambda)

  time.sleep(1)

  obj['text'] = 'hello pyvue'


def test2():
  print('--test2--')

  data = {'ok': False, 'text': 'hello world'}

  obj = Proxy(data)

  def effect_lambda():
    print(obj['text'] if obj['ok'] else 'not')

  effect(effect_lambda)

  obj['text'] = 'hello pyvue'


def test3():
  print('--test3--')

  data = {'foo': 1}

  obj = Proxy(data)

  def effect_lambda():
    obj['foo'] += 1  # 递归

  effect(effect_lambda)


def test4():
  print('--test4--')

  data = {'foo': 1}

  obj = Proxy(data)

  def effect_lambda():
    print(obj['foo'])

  global job_queue
  global threads
  global is_flushing

  job_queue = set()  # 定义一个任务队列
  threads = []
  is_flushing = False  # 一个标志代表是否正在刷新队列

  def flush_job():
    global job_queue
    global threads
    global is_flushing

    # 如果队列正在刷新，则什么都不做
    if is_flushing: return

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

  def scheduler_lambda(fn):
    global job_queue
    job_queue.add(fn)
    threading.Thread(target=flush_job).start()

  effect(effect_lambda, {'scheduler': scheduler_lambda})

  obj['foo'] += 1
  obj['foo'] += 1


def test_computed():
  print('--test computed--')

  data = {
      'foo': 1,
      'bar': 2,
  }

  obj = Proxy(data)

  sum = computed(lambda: obj['foo'] + obj['bar'])

  def effect_lambda():
    # 在副作用函数中读取计算属性的值
    print('sum: ', sum['value'])

  effect(effect_lambda)

  obj['foo'] += 1


def test_watch():
  print('--test watch--')
  data = {
      'foo': 1,
      'bar': 2,
  }

  obj = Proxy(data)

  def get_obj():
    return obj['foo']

  global final_data

  final_data = None

  def watch_cb(new_value, old_value, on_invalidate):
    print(new_value, old_value)
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

  watch(get_obj, watch_cb)

  obj['foo'] += 1
  time.sleep(0.2)
  obj['foo'] += 1

  time.sleep(0.1)
  print('final_data', final_data)


def main():
  test1()
  test2()
  test3()
  test4()
  test_computed()
  test_watch()


main()
