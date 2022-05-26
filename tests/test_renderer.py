import sys
import time
import unittest

from PyQt6.QtWidgets import QApplication, QWidget

from Vue import reactive
from Vue.Proxy import effect
from Vue.Pyqt6RendererOption import Pyqt6RendererOption

from Vue.Renderer import Renderer, RendererOption


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
            {"data": {"type": "QLabel", "props": {"text": "hello world."}}}
        )

        container = {"type": "root"}

        option = Pyqt6RendererOption()

        renderer = Renderer(option)

        w = QWidget()

        w.resize(250, 200)
        w.move(300, 300)
        w.setWindowTitle("hello")

        @effect
        def render():
            renderer.render(vnode["data"], w)

        w.show()

        time.sleep(3)
        
        vnode["data"]["props"]["text"] = "hello pyvue!"

        sys.exit(app.exec())
