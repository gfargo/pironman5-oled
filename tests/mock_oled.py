"""A minimal in-memory stand-in for the real SSD1306 OLED, covering the full
draw surface used by pages/screensavers (see `tests/test_fire_effect.py`'s
`_MockOLED` for the original, narrower version this generalizes).
"""


class _MockDraw:
    def __init__(self):
        self.calls = []

    def point(self, *args, **kwargs):
        self.calls.append(('point', args, kwargs))

    def line(self, *args, **kwargs):
        self.calls.append(('line', args, kwargs))

    def rectangle(self, *args, **kwargs):
        self.calls.append(('rectangle', args, kwargs))

    def __getattr__(self, name):
        def _noop(*args, **kwargs):
            self.calls.append((name, args, kwargs))
        return _noop


class MockOLED:
    def __init__(self):
        self.draw = _MockDraw()
        self.cleared = False
        self.displayed = False

    def clear(self):
        self.cleared = True
        self.draw.calls = []

    def display(self):
        self.displayed = True

    def draw_text(self, *args, **kwargs):
        pass

    def draw_icon(self, *args, **kwargs):
        pass

    def draw_bar_graph_horizontal(self, *args, **kwargs):
        pass

    def draw_bar_graph_vertical(self, *args, **kwargs):
        pass
