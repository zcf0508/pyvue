import sys
import time
import unittest

from PyQt6.QtWidgets import QApplication, QWidget

from Vue import reactive, effect, Pyqt6RendererOption, Renderer, RendererOption


class TestRenderer(unittest.TestCase):
    def test_1(self):

        vnode = reactive(
            {
                "type": "h1",
                "props": {"id": "foo"},
                "children": [
                    {"type": "p", "children": "hello "},
                    {"type": "p", "children": "world."},
                ],
            }
        )

        container = {"type": "root"}

        renderer_option = RendererOption()

        renderer = Renderer(renderer_option)

        @effect
        def render():
            renderer.render(vnode, container)

        vnode["children"] = "hello pyvue!"

    def test_2(self):

        app = QApplication(sys.argv)

        vnode = reactive(
            {
                "type": "QHBoxLayout",
                "children": [
                    {"type": "QPushButton", "props": {"text": "hello "}},
                    {"type": "QPushButton", "props": {"text": "world."}},
                ],
            }
        )

        option = Pyqt6RendererOption()

        renderer = Renderer(option)

        window = QWidget()

        window.resize(250, 200)
        window.move(300, 300)
        window.setWindowTitle("hello")

        @effect
        def render():
            renderer.render(vnode, window)

        window.show()

        time.sleep(1)

        vnode["children"].pop()

        vnode["children"].append({"type": "QPushButton", "props": {"text": "pyvue!"}})

        sys.exit(app.exec())

    def test_3(self):

        app = QApplication(sys.argv)

        def add():
            vnode["children"][0]["props"]["text"] += 1

        vnode = reactive(
            {
                "type": "QVBoxLayout",
                "children": [
                    {"type": "QLabel", "props": {"text": 1}},
                    {"type": "QPushButton", "props": {"text": "Add", "@clicked": add}},
                ],
            }
        )

        option = Pyqt6RendererOption()

        renderer = Renderer(option)

        window = QWidget()

        window.resize(250, 200)
        window.move(300, 300)
        window.setWindowTitle("hello")

        @effect
        def render():
            renderer.render(vnode, window)

        window.show()

        sys.exit(app.exec())
