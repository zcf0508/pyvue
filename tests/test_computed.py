import unittest

from Vue import computed, Proxy, effect


class TestComputed(unittest.TestCase):
    def test_1(self):

        data = {
            "foo": 1,
            "bar": 2,
        }
        obj = Proxy(data)

        sum = computed(lambda: obj["foo"] + obj["bar"])

        def effect_lambda():
            # 在副作用函数中读取计算属性的值
            sum["value"]

        effect(effect_lambda)

        self.assertEqual(sum["value"], 3)

        obj["foo"] += 1

        self.assertEqual(sum["value"], 4)
