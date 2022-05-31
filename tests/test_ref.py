import unittest

from Vue import reactive, ref, to_ref, to_refs, proxy_refs


class TestRef(unittest.TestCase):
    def test_1(self):
        obj = ref(1)

        self.assertEqual(obj["value"], 1)

    def test_2(self):
        obj = reactive({"foo": 1, "bar": 2})

        new_obj = to_refs(obj)

        self.assertEqual(new_obj["foo"].value, 1)
        self.assertEqual(new_obj["bar"].value, 2)

    def test_3(self):
        obj = reactive({"foo": 1, "bar": 2})

        ref_foo = to_ref(obj, "foo")

        self.assertEqual(ref_foo.value, 1)

        ref_foo.value = 100

        self.assertEqual(ref_foo.value, 100)

    def test_4(self):
        obj = reactive({"foo": 1, "bar": 2})

        new_obj = proxy_refs(to_refs(obj))

        self.assertEqual(new_obj["foo"], 1)
