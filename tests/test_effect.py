import sys
import threading
import unittest
import time

from Vue.Proxy import Proxy, effect


class TestEffect(unittest.TestCase):

  def test_1(self):
    global test_1_value

    test_1_value = 1

    data = {'text': 'hello world'}
    obj = Proxy(data)

    def effect_lambda():
      global test_1_value

      obj['text']
      test_1_value += 1

    effect(effect_lambda)

    self.assertEqual(test_1_value, 2)

    time.sleep(1)

    obj['text'] = 'hello pyvue'

    self.assertEqual(test_1_value, 3)

  def test_2(self):
    global test_2_value

    test_2_value = 1

    data = {'ok': False, 'text': 'hello world'}
    obj = Proxy(data)

    def effect_lambda():
      global test_2_value

      obj['text'] if obj['ok'] else 'not'
      test_2_value += 1

    effect(effect_lambda)

    self.assertEqual(test_2_value, 2)

    obj['text'] = 'hello pyvue'

    self.assertEqual(test_2_value, 2)

  def test_3(self):
    data = {'foo': 1}
    obj = Proxy(data)

    def effect_lambda():
      obj['foo'] += 1  # 递归

    effect(effect_lambda)

    self.assertEqual(obj['foo'], 2)

  def test4(self):
    global job_queue
    global threads
    global is_flushing
    global test_4_value

    test_4_value = 1

    data = {'foo': 1}
    obj = Proxy(data)

    def effect_lambda():
      global test_4_value

      obj['foo']
      test_4_value += 1

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

    self.assertEqual(test_4_value, 2)


if __name__ == '__main__':
  unittest.main()
