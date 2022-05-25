import binascii
import os
from typing import Any, Union
from unittest.mock import patch

Text = binascii.hexlify(os.urandom(8)).decode("utf-8")
Fragment = binascii.hexlify(os.urandom(8)).decode("utf-8")


class RendererOption:
    def create_element(self, tag: str):
        print(f"创建元素 {tag}")
        return {"tag": tag}
        pass

    def mount_element(self, vnode: dict, container: dict):
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
        pass

    def set_element_text(self, el: dict, text: str):
        print(f"设置 {el} 的文本内容: {text}")
        el.setdefault("text", text)
        pass

    def insert(self, el: dict, parent: dict, anchor=None):
        print(f"将 {el} 添加到 {parent} 下")
        parent.setdefault("children", el)
        pass

    def create_text(self, text: str):
        pass

    def set_text(self, el, text: str):
        pass

    def patch(self, n1: Union[dict, None], n2: dict, container: dict):
        # 如果 n1 存在，则对比 n1 和 n2 的类型
        if n1 and n1["type"] != n2["type"]:
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

    def patch_props(self, el: dict, key: str, pre_val: Any, next_val: Any):
        print(f"给 {el} 设置属性 {key} = {next_val}")
        el.setdefault(key, next_val)
        pass

    def unmount(self, vnode: dict, container: dict):
        if vnode["type"] == Fragment:
            for child in vnode["children"]:
                self.unmount(child, container)
            return
        el = vnode["el"]
        del container[el]
        print(f"移除 {el}")

    def path_children(self, n1: dict, n2: dict, container: dict):
        # 判断新子节点的类型是否为文本节点
        if isinstance(n2.get("children", ""), str):
            # 旧子节点的类型有三种可能：没有子节点，文本子节点，以及一组子节点
            # 只有当旧子节点为一组子节点时，才需要逐个卸载，其它情况下什么都不需要做
            if isinstance(n1.get("children", ""), list):
                for child in n1["children"]:
                    self.unmount(child, container)
            self.set_element_text(container, n2.get("children", ""))
        elif isinstance(n2.get("children", ""), list):
            # 说明新子节点是一组子节点
            if isinstance(n1.get("children", ""), list):
                # TODO:diff
                for child in n1["children"]:
                    self.unmount(child, container)
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

        pass

    def patch_element(self, n1: dict, n2: dict):
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


class Renderer:
    _vnode = None

    def __init__(self, option: RendererOption):
        self._create_element = option.create_element
        self._set_element_text = option.set_element_text
        self._insert = option.insert
        self._patch_props = option.patch_props
        self._patch_element = option.patch_element
        self._unmount = option.unmount
        self._patch = option.patch
        self._mount_element = option.mount_element

    def render(self, vnode, container: dict):
        if vnode:
            self._patch(container.get("_vnode", None), vnode, container)
        else:
            if container.get("_vnode", None):
                self._unmount(container["_vnode"], container)
        container.setdefault("_vnode", vnode)
        pass
