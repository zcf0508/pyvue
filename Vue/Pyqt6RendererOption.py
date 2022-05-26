import copy
from typing import Union

from PyQt6.QtWidgets import QWidget, QLayout

from Vue.Proxy import Proxy
from Vue.Renderer import Fragment, RendererOption, Text


class Pyqt6RendererOption(RendererOption):
    _engine = "pyqt6"

    def render(self, vnode, container):
        if vnode:
            self.patch(
                container._vnode if hasattr(container, "_vnode") else None,
                vnode,
                container,
            )
        else:
            if container._vnode:
                self.unmount(container._vnode, container)

        container._vnode = Proxy.raw(vnode)
        pass

    def create_element(self, tag: str):
        PyQt6 = __import__("PyQt6.QtWidgets", fromlist=[])
        QtWidgets = PyQt6.QtWidgets
        element = getattr(QtWidgets, tag)()
        return element

    def mount_element(self, vnode, container):

        el = self.create_element(vnode["type"])
        vnode.setdefault("el", el)
        if isinstance(vnode.get("children", ""), str):
            self.set_element_text(el, vnode.get("children", ""))
        elif isinstance(vnode.get("children", ""), list):
            for child in vnode.get("children", ""):
                self.patch(None, child, el)

        if vnode.get("props", None):
            for key, val in vnode["props"].items():
                self.patch_props(el, key, None, val)

        self.insert(el, container)

    def set_element_text(self, el, text):
        pass

    def insert(self, el, parent, anchor=None):
        print(el)
        print(parent)
        if hasattr(parent, "setLayout") and isinstance(el, QLayout):
            parent.setLayout(el)
        elif hasattr(parent, "addWidget") and isinstance(el, QWidget):
            parent.addWidget(el)
        else:
            el.setParent(parent)

    def create_text(self, text):
        pass

    def set_text(self, el, text):
        pass

    def patch(self, n1: Union[dict, None], n2: dict, container):
        # 如果 n1 存在，则对比 n1 和 n2 的类型
        if n1 and n1["type"] != n2["type"]:
            # print(n1)
            self.unmount(n1, container)
            n1 = None

        type = n2["type"]
        # 如果新 vnode 的类型是 Text ，则说明该 vnode 描述的是文本节点
        if type == Text:
            if not n1:
                el = n2["el"] = self.create_text(n2["children"])
                self.insert(el, container)
            else:
                el = n2["el"] = n1["el"]
                if n2["children"] != n1["children"]:
                    self.set_text(el, n2["children"])
            pass
        elif type == Fragment:
            # 处理 Fragment 类型的 vnode
            if not n1:
                for child in n2["children"]:
                    self.patch(None, child, container)
            else:
                self.path_children(n1, n2, container)
        # 如果 n2["type"] 的值是字符串类型，则它描述的是普通标签元素
        elif isinstance(type, str):
            if not n1:
                self.mount_element(n2, container)
            else:
                self.patch_element(n1, n2)
                pass
        elif isinstance(type, dict):
            # 如果 n2["type"] 的值是字典，则它描述的是组件
            pass
        else:
            # 其它类型
            pass
        pass
        pass

    def patch_props(self, el, key, pre_val, next_val):
        if key == "text":
            el.setText(next_val)
        pass

    def unmount(self, vnode, container):
        pass

    def path_children(self, n1, n2, container):
        pass

    def patch_element(self, n1, n2):
        el = n2["el"] = n1["el"]
        old_props = n1["props"]
        new_props = n2["props"]
        # 第一步，更新 props
        for key, val in new_props.items():
            self.patch_props(el, key, old_props.get(key, None), val)
        for key, val in old_props.items():
            if key not in new_props:
                self.patch_props(el, key, val, None)

        # 第二步，更新 children
        self.path_children(n1, n2, el)
        pass
