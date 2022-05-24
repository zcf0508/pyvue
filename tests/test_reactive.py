import unittest

from Vue import reactive, shallow_reactive, readonly, shallow_readonly
from Vue.Proxy import effect


class TestReactive(unittest.TestCase):
    def test_dict_1(self):
        global test_1_value
        test_1_value = 1

        data = {"foo": 1}
        obj = reactive(data)

        def effect_lambda():
            global test_1_value

            for key in obj:
                key

            test_1_value += 1

        effect(effect_lambda)

        self.assertEqual(test_1_value, 2)

        obj.setdefault("baz", []).append(1)

        self.assertEqual(test_1_value, 3)

        obj.pop("foo2", None)

        self.assertEqual(test_1_value, 3)

        obj["foo"] += 1

        self.assertEqual(test_1_value, 3)

    def test_dict_2(self):
        global test_1_value
        test_1_value = 1

        data = {"foo": 1}
        obj = reactive(data)

        def effect_lambda():
            global test_1_value

            obj_iter = obj.__iter__()

            test_1_value += 1

        effect(effect_lambda)

        self.assertEqual(test_1_value, 2)

        obj.setdefault("baz", []).append(1)

        self.assertEqual(test_1_value, 3)

        obj.pop("foo2", None)

        self.assertEqual(test_1_value, 3)

        obj["foo"] += 1

        self.assertEqual(test_1_value, 3)

    def test_dict_3(self):
        global test_1_value
        test_1_value = 1

        data = {"foo": 1}
        obj = reactive(data)

        def effect_lambda():
            global test_1_value

            for key, value in obj.items():
                key
                value

            test_1_value += 1

        effect(effect_lambda)

        self.assertEqual(test_1_value, 2)

        obj.setdefault("baz", []).append(1)

        self.assertEqual(test_1_value, 3)

        obj.pop("foo2", None)

        self.assertEqual(test_1_value, 3)

        obj["foo"] += 1

        self.assertEqual(test_1_value, 4)

    def test_dict_4(self):
        global test_1_value
        test_1_value = 1

        data = {"foo": {"bar": 1}}
        obj = reactive(data)

        def effect_lambda():
            global test_1_value

            obj["foo"]["bar"]

            test_1_value += 1

        effect(effect_lambda)

        self.assertEqual(test_1_value, 2)

        obj["foo"]["bar"] += 1

        self.assertEqual(test_1_value, 3)

    def test_dict_5(self):
        global test_1_value
        test_1_value = 1

        data = {"foo": {"bar": 1}}
        obj = shallow_reactive(data)

        def effect_lambda():
            global test_1_value

            obj["foo"]["bar"]

            test_1_value += 1

        effect(effect_lambda)

        self.assertEqual(test_1_value, 2)

        obj["foo"]["bar"] += 1

        self.assertEqual(test_1_value, 2)

    def test_dict_6(self):
        global test_1_value
        test_1_value = 1

        data = {"foo": {"bar": 1}}
        obj = readonly(data)

        def effect_lambda():
            global test_1_value

            obj["foo"]["bar"]

            test_1_value += 1

        effect(effect_lambda)

        self.assertEqual(test_1_value, 2)

        obj["foo"]["bar"] += 1

        self.assertEqual(test_1_value, 2)

    def test_dict_7(self):
        global test_1_value
        test_1_value = 1

        data = {"foo": {"bar": 1}}
        obj = shallow_readonly(data)

        def effect_lambda():
            global test_1_value

            obj["foo"]["bar"]

            test_1_value += 1

        effect(effect_lambda)

        self.assertEqual(test_1_value, 2)

        obj["foo"]["bar"] += 1

        self.assertEqual(test_1_value, 2)
