import unittest
from Vue import reactive
from Vue.Proxy import effect

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
