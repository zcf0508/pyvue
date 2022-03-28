import time
from Vue.Proxy import Proxy, effect
from Vue import computed, watch


def test_computed():
  print('--test computed--')

  data = {
      'foo': 1,
      'bar': 2,
  }

  obj = Proxy(data)

  sum = computed(lambda: obj['foo'] + obj['bar'])

  def effect_lambda():
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
  test_computed()
  test_watch()


main()
