# modules/low_stock_alert.py
from database.db_manager import DatabaseManager
from database.models import Product
from kivy.clock import Clock
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView


class LowStockAlert:
    def __init__(self, product_manager, on_navigate=None):
        self.product_manager = product_manager
        self.on_navigate = on_navigate
        self.last_check = None

    def check_low_stock(self, threshold=5):
        """Аз калган товарларды текшерүү"""
        try:
            products = self.product_manager.get_all_products ()
            low_stock = [p for p in products if p.stock <= threshold and p.stock > 0]
            out_of_stock = [p for p in products if p.stock == 0]

            if low_stock or out_of_stock:
                self.show_alert ( low_stock, out_of_stock )
                return True, low_stock, out_of_stock
            return False, [], []
        except Exception as e:
            print ( f"Low stock check error: {e}" )
            return False, [], []

    def show_alert(self, low_stock, out_of_stock):
        """Эскертүү көрсөтүү"""
        content = BoxLayout ( orientation='vertical', spacing=10, padding=10 )

        if out_of_stock:
            content.add_widget ( Label ( text="❌ ТҮГӨНГӨН ТОВАРЛАР:", color=(1, 0, 0, 1), font_size=14, bold=True ) )
            for p in out_of_stock[:10]:
                btn = Button (
                    text=f"{p.name} - 0 {p.unit_type.value}",
                    size_hint_y=None,
                    height=35,
                    background_color=(0.8, 0.2, 0.2, 0.8)
                )
                if self.on_navigate:
                    btn.bind ( on_press=lambda x, pid=p.id: self.on_navigate ( 'products' ) )
                content.add_widget ( btn )

        if low_stock:
            if out_of_stock:
                content.add_widget ( Spacer ( 1, 10 ) )
            content.add_widget (
                Label ( text="⚠️ АЗ КАЛГАН ТОВАРЛАР:", color=(1, 0.5, 0, 1), font_size=14, bold=True ) )
            for p in low_stock[:10]:
                btn = Button (
                    text=f"{p.name} - {p.stock} {p.unit_type.value}",
                    size_hint_y=None,
                    height=35,
                    background_color=(0.8, 0.5, 0, 0.8)
                )
                if self.on_navigate:
                    btn.bind ( on_press=lambda x, pid=p.id: self.on_navigate ( 'products' ) )
                content.add_widget ( btn )

        scroll = ScrollView ()
        scroll.add_widget ( content )

        popup = Popup (
            title="⚠️ КАМПА ЭСКЕРТҮҮСҮ",
            content=scroll,
            size_hint=(0.8, 0.6)
        )

        close_btn = Button ( text="ТҮШҮНДҮМ", size_hint_y=0.1 )
        close_btn.bind ( on_press=popup.dismiss )
        content.add_widget ( close_btn )

        popup.open ()