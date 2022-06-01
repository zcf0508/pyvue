from typing import Any, Callable, Union
from warnings import warn

from Vue.renderer.Renderer import Fragment, Slot


class PyQt6VComponent:
    prop_keys: set[str] = set()

    def __init__(self, type: str, **kwargs: dict[str, Any]) -> None:
        self._id = id(self)
        self.type = type
        self.props: dict[str, Any] = {}
        self.children: list = []
        self.set_props(kwargs)

    def set_props(self, props: dict):
        for key, val in props.items():
            if key not in iter(self.prop_keys):
                warn(f"组件不支持{key}属性，可能不会生效")
            if key in self.props.keys():
                warn(f"重复属性，{key}的原始值{self.props[key]}将被赋值为{val}")
                self.props[key] = val
            else:
                self.props.setdefault(key, val)

    def add_prop(self, key: str, val: Any):
        if key in self.props.keys():
            self.props[key] = val
        else:
            warn(f"不存在{key}属性，将添加属性{key}并将值设为{val}")
            self.props.setdefault(key, val)

    def remove_prop(self, key):
        if key in self.props.keys():
            self.props.pop(key)
        else:
            warn(f"不存在{key}属性")

    def add_child(self, child):
        if isinstance(child, PyQt6VComponent):
            self.children.append(child)
        else:
            raise TypeError(f"{child}不是组件")

    def add_children(self, children):
        for child in children:
            if isinstance(child, PyQt6VComponent):
                self.children.append(child)
            else:
                raise TypeError(f"{child}不是组件")

    def remove_child(self, child_id):
        for child in self.children:
            if child_id == child._id:
                self.children.pop(self.children.index(child))
                break
        else:
            warn(f"不存在id为{child_id}的子组件")

    def __call__(self, *args):
        """添加子组件"""
        for child in iter(args):
            if isinstance(child, PyQt6VComponent):
                self.children.append(child)
            else:
                raise TypeError(f"{child}不是组件")

        return self

    def __str__(self):
        return f"PyQt6VComponent<{self.type}> id:{self._id} props:{self.props} children:{[str(child) for child in self.children]}"

    __repr__ = __str__

    def to_dict(self):
        props = {}
        for key, val in self.props.items():
            if val != None:
                props.setdefault(key, val)

        return {
            "type": self.type,
            "props": props,
            "children": [child.to_dict() for child in self.children],
        }


class VSlot(PyQt6VComponent):
    slot_name = ""
    prop_keys: set[str] = set()

    def __init__(self, slot_name="default", **kwargs) -> None:
        self.slot_name = slot_name
        super().__init__(Slot, **kwargs)

    def __str__(self):
        return f"PyQt6VComponent<{self.type}> id:{self._id} slot_name:{self.slot_name} children:{[child.__str__() for child in self.children]}"

    __repr__ = __str__


class VFragment(PyQt6VComponent):
    prop_keys: set[str] = set()

    def __init__(self, **kwargs) -> None:
        super().__init__(Fragment, **kwargs)

    def set_slots(
        self, name="default", slots: Union[list[PyQt6VComponent], "VFragment"] = []
    ):
        for child in self.children[:]:
            if child.type == Slot and child.slot_name == name:
                index = self.children.index(child)
                for slot_child in slots if isinstance(slots, list) else slots.children:
                    self.children.insert(index, slot_child)
                    index += 1
                self.children.remove(child)
                break
        else:
            warn(f"没有找到名为{name}的slot")

        return self


class VWidget(PyQt6VComponent):
    prop_keys: set[str] = {"x", "y"}

    def __init__(self, **kwargs) -> None:
        super().__init__("QWidget", **kwargs)


class VLabel(PyQt6VComponent):
    prop_keys: set[str] = {"text", "@clicked"}

    def __init__(self, **kwargs) -> None:
        super().__init__("QLabel", **kwargs)


class VHBoxLayout(PyQt6VComponent):
    prop_keys: set[str] = set()

    def __init__(self, **kwargs) -> None:
        super().__init__("QHBoxLayout", **kwargs)
