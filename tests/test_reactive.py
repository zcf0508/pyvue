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

        self.assertEqual(test_1_value, 3)

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

    def test_dict_8(self):
        global test_1_value
        test_1_value = 1

        data = {"foo": 1}
        obj = reactive(data)

        def effect_lambda():
            global test_1_value

            "foo" in obj

            test_1_value += 1

        effect(effect_lambda)

        self.assertEqual(test_1_value, 2)

        obj["foo"] += 1

        self.assertEqual(test_1_value, 2)

        obj.setdefault("baz", []).append(1)

        self.assertEqual(test_1_value, 3)

    def test_dict_9(self):
        global test_1_value
        test_1_value = 1

        data = {"foo": 1}
        obj = reactive(data)

        def effect_lambda():
            global test_1_value

            for key in obj.keys():
                pass

            test_1_value += 1

        effect(effect_lambda)

        self.assertEqual(test_1_value, 2)

        obj["foo"] += 1

        self.assertEqual(test_1_value, 2)

        obj.setdefault("baz", []).append(1)

        self.assertEqual(test_1_value, 3)

    def test_dict_10(self):
        global test_1_value
        test_1_value = 1

        data = {"foo": 1}
        obj = reactive(data)

        def effect_lambda():
            global test_1_value

            for key in obj.keys():
                pass

            test_1_value += 1

        effect(effect_lambda)

        self.assertEqual(test_1_value, 2)

        obj["foo"] += 1

        self.assertEqual(test_1_value, 2)

        obj.update({"bar": 2})

        self.assertEqual(test_1_value, 3)

    def test_dict_11(self):
        global test_1_value
        test_1_value = 1

        data = {"foo": 1}
        obj = reactive(data)

        def effect_lambda():
            global test_1_value

            for value in obj.values():
                pass

            test_1_value += 1

        effect(effect_lambda)

        self.assertEqual(test_1_value, 2)

        obj["foo"] += 1

        self.assertEqual(test_1_value, 2)

        obj.update({"bar": 2})

        self.assertEqual(test_1_value, 3)

        obj.popitem()

        self.assertEqual(test_1_value, 4)

    def test_list_1(self):
        global test_1_value
        test_1_value = 1

        data = ["foo"]
        obj = reactive(data)

        def effect_lambda():
            global test_1_value

            obj[0]

            test_1_value += 1

        effect(effect_lambda)

        self.assertEqual(test_1_value, 2)

        obj[0] = "bar"

        self.assertEqual(test_1_value, 3)

    def test_list_2(self):
        global test_1_value
        test_1_value = 1

        data = ["foo", "bar"]
        obj = reactive(data)

        def effect_lambda():
            global test_1_value

            for item in obj:
                # print(item)
                pass

            test_1_value += 1

        effect(effect_lambda)

        self.assertEqual(test_1_value, 2)

        obj.append("baz")

        self.assertEqual(test_1_value, 3)

    def test_list_3(self):
        global test_1_value
        test_1_value = 1

        data = ["foo", "bar"]
        obj = reactive(data)

        def effect_lambda():
            global test_1_value

            for index, item in enumerate(obj):
                # print(item)
                pass

            test_1_value += 1

        effect(effect_lambda)

        self.assertEqual(test_1_value, 2)

        obj.pop()

        self.assertEqual(test_1_value, 3)

    def test_list_4(self):
        global test_1_value
        test_1_value = 1

        data = ["foo", "bar"]
        obj = reactive(data)

        def effect_lambda():
            global test_1_value

            len(obj)

            test_1_value += 1

        effect(effect_lambda)

        self.assertEqual(test_1_value, 2)

        obj.pop()

        self.assertEqual(test_1_value, 3)

    def test_list_5(self):
        global test_1_value
        test_1_value = 1

        data = ["foo", "bar"]
        obj = reactive(data)

        def effect_lambda():
            global test_1_value

            for index, item in enumerate(obj):
                # print(item)
                pass

            test_1_value += 1

        effect(effect_lambda)

        self.assertEqual(test_1_value, 2)

        obj.pop()

        self.assertEqual(test_1_value, 3)

    def test_list_6(self):
        global test_1_value
        test_1_value = 1

        data = [1, 2]
        obj = reactive(data)

        def effect_lambda():
            global test_1_value

            obj.count(1)

            test_1_value += 1

        effect(effect_lambda)

        self.assertEqual(test_1_value, 2)

        obj.pop()

        self.assertEqual(test_1_value, 3)

    def test_list_7(self):
        global test_1_value
        test_1_value = 1

        data = [1, 2, 3]
        obj = reactive(data)

        def effect_lambda():
            global test_1_value

            obj.index(3)

            test_1_value += 1

        effect(effect_lambda)

        self.assertEqual(test_1_value, 2)

        obj.insert(1, 2)

        self.assertEqual(test_1_value, 3)

    def test_list_8(self):
        global test_1_value
        test_1_value = 1

        data = [1, 2, 3, 4]
        obj = reactive(data)

        def effect_lambda():
            global test_1_value

            obj.index(3)

            test_1_value += 1

        effect(effect_lambda)

        self.assertEqual(test_1_value, 2)

        obj.reverse()

        self.assertEqual(test_1_value, 2 + len(obj) - (len(obj) % 2))  # 反转会导致整个列表都变化

    def test_list_9(self):
        global test_1_value
        test_1_value = 1

        data = [1, 2, 3, 4]
        obj = reactive(data)

        def effect_lambda():
            global test_1_value

            obj.index(3)

            test_1_value += 1

        effect(effect_lambda)

        self.assertEqual(test_1_value, 2)

        obj.sort(reverse=True)

        self.assertEqual(test_1_value, 2 + len(obj) - (len(obj) % 2))  # 反转会导致整个列表都变化

    def test_set_1(self):
        global test_1_value
        test_1_value = 1

        data = {1, 2, 3, 4}
        obj = reactive(data)

        def effect_lambda():
            global test_1_value

            for item in obj:
                pass

            test_1_value += 1

        effect(effect_lambda)

        self.assertEqual(test_1_value, 2)

        obj.add(1)

        self.assertEqual(test_1_value, 2)

        obj.add(5)

        self.assertEqual(test_1_value, 3)

    def test_set_2(self):
        global test_1_value
        test_1_value = 1

        data = {1, 2, 3, 4}
        obj = reactive(data)

        def effect_lambda():
            global test_1_value

            for item in obj:
                pass

            test_1_value += 1

        effect(effect_lambda)

        self.assertEqual(test_1_value, 2)

        obj.difference_update({1, 2})

        self.assertEqual(test_1_value, 4)

        obj.difference({3, 4})

        self.assertEqual(test_1_value, 4)

    def test_set_3(self):
        global test_1_value
        test_1_value = 1

        data = {1, 2, 3, 4}
        obj = reactive(data)

        def effect_lambda():
            global test_1_value

            for item in obj:
                pass

            test_1_value += 1

        effect(effect_lambda)

        self.assertEqual(test_1_value, 2)

        obj.discard(2)

        self.assertEqual(test_1_value, 3)

    def test_set_4(self):
        global test_1_value
        test_1_value = 1

        data = {1, 2, 3, 4}
        obj = reactive(data)

        def effect_lambda():
            global test_1_value

            for item in obj:
                pass

            test_1_value += 1

        effect(effect_lambda)

        self.assertEqual(test_1_value, 2)

        obj.intersection_update({1, 2})

        self.assertEqual(test_1_value, 4)

        obj.intersection({3, 4})

        self.assertEqual(test_1_value, 4)

    def test_set_5(self):
        global test_1_value
        test_1_value = 1

        data = {1, 2, 3, 4}
        obj = reactive(data)

        def effect_lambda():
            global test_1_value

            print(obj.isdisjoint({4}))

            test_1_value += 1

        effect(effect_lambda)

        self.assertEqual(test_1_value, 2)

        obj.discard(4)

        self.assertEqual(test_1_value, 3)

    def test_set_6(self):
        global test_1_value
        test_1_value = 1

        data = {1, 2, 3, 4}
        obj = reactive(data)

        def effect_lambda():
            global test_1_value

            1 in obj

            test_1_value += 1

        effect(effect_lambda)

        self.assertEqual(test_1_value, 2)

        obj.remove(1)

        self.assertEqual(test_1_value, 3)

        obj.pop()

        self.assertEqual(test_1_value, 4)

    def test_set_7(self):
        global test_1_value
        test_1_value = 1

        data = {1, 2, 3, 4}
        obj = reactive(data)

        def effect_lambda():
            global test_1_value

            for item in obj:
                pass

            test_1_value += 1

        effect(effect_lambda)

        self.assertEqual(test_1_value, 2)

        obj.symmetric_difference_update({1, 2, 5})

        self.assertEqual(test_1_value, 5)

        obj.symmetric_difference({3, 4, 5})

        self.assertEqual(test_1_value, 5)
    
    def test_set_8(self):
        global test_1_value
        test_1_value = 1

        data = {1, 2, 3, 4}
        obj = reactive(data)

        def effect_lambda():
            global test_1_value

            for item in obj:
                pass

            test_1_value += 1

        effect(effect_lambda)

        self.assertEqual(test_1_value, 2)

        obj.update({2})

        self.assertEqual(test_1_value, 2)

        obj.update({5})

        self.assertEqual(test_1_value, 3)
