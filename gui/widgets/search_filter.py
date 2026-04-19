# gui/widgets/search_filter.py
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.button import Button


class SearchFilter ( BoxLayout ):
    def __init__(self, on_search, categories=None, **kwargs):
        super ().__init__ ( **kwargs )
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = 50
        self.spacing = 10
        self.padding = 5
        self.on_search = on_search

        self.search_input = TextInput ( hint_text="🔍 Издөө...", multiline=False, size_hint_x=0.5 )
        self.search_input.bind ( on_text_validate=self.do_search )
        self.add_widget ( self.search_input )

        if categories:
            self.category_spinner = Spinner ( text="Бардык категориялар", values=categories, size_hint_x=0.3 )
            self.category_spinner.bind ( text=self.do_search )
            self.add_widget ( self.category_spinner )

        search_btn = Button ( text="Издөө", size_hint_x=0.2, background_color=(0.3, 0.6, 0.9, 1) )
        search_btn.bind ( on_press=self.do_search )
        self.add_widget ( search_btn )

    def do_search(self, instance):
        search_text = self.search_input.text
        category = getattr ( self, 'category_spinner', None )
        category_text = category.text if category and category.text != "Бардык категориялар" else None
        self.on_search ( search_text, category_text )