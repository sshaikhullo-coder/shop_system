# gui/widgets/stat_card.py
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.graphics import Color, RoundedRectangle


class StatCard ( BoxLayout ):
    def __init__(self, title, value, color="#3498db", icon="📊", **kwargs):
        super ().__init__ ( **kwargs )
        self.orientation = 'vertical'
        self.padding = 10
        self.spacing = 5
        self.size_hint_y = None
        self.height = 100

        with self.canvas.before:
            Color ( *self.hex_to_rgb ( color ), 1 )
            RoundedRectangle ( size=self.size, pos=self.pos, radius=[10] )
            self.bind ( pos=self.update_rect, size=self.update_rect )

        self.add_widget ( Label ( text=f"{icon} {title}", font_size=12, color=(1, 1, 1, 1) ) )
        self.add_widget ( Label ( text=str ( value ), font_size=28, bold=True, color=(1, 1, 1, 1) ) )

    def hex_to_rgb(self, hex_color):
        hex_color = hex_color.lstrip ( '#' )
        return tuple ( int ( hex_color[i:i + 2], 16 ) / 255.0 for i in (0, 2, 4) )

    def update_rect(self, instance, value):
        self.canvas.before.children[0].size = instance.size
        self.canvas.before.children[0].pos = instance.pos