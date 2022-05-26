import binascii
import copy
import os
from typing import Dict, Union

from PyQt6.QtWidgets import QWidget, QLayout

from Vue.Proxy import Proxy
from Vue.Renderer import Fragment, RendererOption, Text


class ElmentAgent:
    elements: Dict = dict()

    def take_element(self, id):
        for key, val in self.elements.items():
            if key == id:
                return val

        return None

    def save_element(self, element):
        if element in self.elements.values():
            for key, val in self.elements.items():
                if val == element:
                    return key
        while True:
            id = binascii.hexlify(os.urandom(8)).decode("utf-8")
            if id not in self.elements.keys():
                break

        self.elements.setdefault(id, element)
        return id

    def delete_element(self, id):
        if id in self.elements.keys():
            del self.elements[id]
            return True
        else:
            return False


class Pyqt6RendererOption(RendererOption):
    _engine = "pyqt6"
    element_agent = ElmentAgent()

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

        container._vnode = copy.deepcopy(Proxy.raw(vnode))
        pass

    def create_element(self, tag: str):
        PyQt6 = __import__("PyQt6.QtWidgets", fromlist=[])
        QtWidgets = PyQt6.QtWidgets
        element = getattr(QtWidgets, tag)()
        return element

    def mount_element(self, vnode, container):
        el = self.create_element(vnode["type"])
        vnode.setdefault("el", self.element_agent.save_element(el))
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
            self.unmount(n1)
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

    def unmount(self, vnode):
        if vnode["type"] == Fragment:
            for child in vnode["children"]:
                self.unmount(child, vnode)
            return

        el = self.element_agent.take_element(vnode["el"])
        el.setParent(None)

    def path_children(self, n1, n2, container):
        # 判断新子节点的类型是否为文本节点
        if isinstance(n2.get("children", ""), str):
            # 旧子节点的类型有三种可能：没有子节点，文本子节点，以及一组子节点
            # 只有当旧子节点为一组子节点时，才需要逐个卸载，其它情况下什么都不需要做
            if isinstance(n1.get("children", ""), list):
                for child in n1["children"]:
                    self.unmount(child, container)
            self.set_element_text(container, n2.get("children", ""))
        elif isinstance(n2.get("children", ""), list) or isinstance(
            n2.get("children", "").__dict__["_data"], list
        ):
            # 说明新子节点是一组子节点
            if isinstance(n1.get("children", ""), list) or isinstance(
                n1.get("children", "").__dict__["_data"], list
            ):
                # TODO:diff
                for child in n1["children"]:
                    self.unmount(child)
                for child in n2["children"]:
                    self.patch(None, child, container)
                pass
            else:
                # 旧节点要么是文本子节点，要么不存在
                # 无论哪种情况，我们都只需要将容器清空，然后将新的一组子节点逐个挂载
                self.set_element_text(container, "")
                for child in n2["children"]:
                    self.patch(None, child, container)
        else:
            # 代码运行到这里，说明新子节点不存在
            # 旧子节点是一组子节点，只需逐个卸载即可
            if isinstance(n1.get("children", ""), list):
                for child in n1["children"]:
                    self.unmount(child, container)
            else:
                self.set_element_text(container, "")

    def patch_element(self, n1, n2):
        el = n1["el"]
        n2["el"] = n1["el"]
        old_props = n1.get("props", {})
        new_props = n2.get("props", {})

        # 第一步，更新 props
        for key, val in new_props.items():
            self.patch_props(el, key, old_props.get(key, None), val)
        for key, val in old_props.items():
            if key not in new_props:
                self.patch_props(el, key, val, None)

        # 第二步，更新 children
        self.path_children(n1, n2, self.element_agent.take_element(el))
        pass
