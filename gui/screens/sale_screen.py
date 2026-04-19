from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner
from kivy.graphics import Color, RoundedRectangle
from database.models import PaymentType
from datetime import datetime


class SaleScreen ( BoxLayout ):
    def __init__(self, user_data, product_manager, sales_manager, on_back, **kwargs):
        super ().__init__ ( **kwargs )
        self.orientation = 'vertical'
        self.user_data = user_data
        self.product_manager = product_manager
        self.sales_manager = sales_manager
        self.on_back = on_back
        self.current_product = None

        self.build_ui ()

    def build_ui(self):
        """UI түзүү"""
        self.create_header ()
        self.create_product_search ()
        self.create_cart_display ()
        self.create_payment_section ()

        self.update_cart_display ()

    def create_header(self):
        header = BoxLayout ( size_hint_y=0.08, padding=10, spacing=10 )
        with header.canvas.before:
            Color ( 0.2, 0.4, 0.6, 1 )
            RoundedRectangle ( size=header.size, pos=header.pos, radius=[10] )

        back_btn = Button ( text="← АРТКА", size_hint_x=0.15, background_color=(0.5, 0.5, 0.5, 1), bold=True )
        back_btn.bind ( on_press=lambda x: self.on_back () )
        header.add_widget ( back_btn )

        header.add_widget (
            Label ( text=f"🛒 САТУУ - {self.user_data['full_name']}", color=(1, 1, 1, 1), font_size=18, bold=True ) )

        self.add_widget ( header )

    def create_product_search(self):
        search_box = BoxLayout ( size_hint_y=0.1, padding=10, spacing=10 )

        self.search_input = TextInput ( hint_text="Штрихкод же товар атын жазыңыз", multiline=False, font_size=14 )
        self.search_input.bind ( on_text_validate=self.search_product )
        search_box.add_widget ( self.search_input )

        search_btn = Button ( text="🔍 ИЗДӨӨ", size_hint_x=0.2, background_color=(0.3, 0.6, 0.9, 1), bold=True )
        search_btn.bind ( on_press=self.search_product )
        search_box.add_widget ( search_btn )

        self.add_widget ( search_box )

    def search_product(self, instance):
        """Товарды издөө (штрихкод же аты боюнча)"""
        search_text = self.search_input.text.strip ()

        if not search_text:
            return

        # Бир аз күтүү (штрихкод сканерден кийин)
        from kivy.clock import Clock

        def do_search(dt):
            products = self.product_manager.search_products ( search_text )

            if products:
                # Эгер бир гана товар табылса, түздөн-түз кошуу терезесин ачуу
                if len ( products ) == 1:
                    self.current_product = products[0]
                    self.show_quantity_input ()
                else:
                    self.show_product_selection ( products )

                # Издөө талаасын тазалоо (кийинки сканер үчүн)
                self.search_input.text = ""
            else:
                self.show_popup ( "Товар табылган жок", f"'{search_text}' штрихкоду же аты менен товар жок" )
                # Издөө талаасын тазалоо
                self.search_input.text = ""

        # Кыска күтүү (штрихкод сканерден кийин)
        Clock.schedule_once ( do_search, 0.1 )

    def show_product_selection(self, products):
        content = BoxLayout ( orientation='vertical', spacing=10, padding=10 )

        scroll = ScrollView ()
        list_layout = BoxLayout ( orientation='vertical', size_hint_y=None, spacing=5 )
        list_layout.bind ( minimum_height=list_layout.setter ( 'height' ) )

        for product in products:
            btn = Button (
                text=f"📦 {product.name}\n💵 {product.price} сом | 📦 {product.stock} {product.unit_type.value}",
                size_hint_y=None,
                height=60,
                background_color=(0.9, 0.9, 0.9, 1),
                color=(0, 0, 0, 1),
                font_size=12
            )
            btn.bind ( on_press=lambda x, p=product: self.select_product ( p ) )
            list_layout.add_widget ( btn )

        scroll.add_widget ( list_layout )
        content.add_widget ( scroll )

        popup = Popup ( title="Товар тандаңыз", content=content, size_hint=(0.8, 0.7) )
        popup.open ()

    def select_product(self, product):
        self.current_product = product
        self.show_quantity_input ()

    def show_quantity_input(self):
        content = BoxLayout ( orientation='vertical', spacing=10, padding=10 )

        content.add_widget ( Label ( text=f"📦 {self.current_product.name}", font_size=16, bold=True ) )
        content.add_widget ( Label ( text=f"💵 Баасы: {self.current_product.price} сом", font_size=14 ) )
        content.add_widget (
            Label ( text=f"📊 Складда: {self.current_product.stock} {self.current_product.unit_type.value}",
                    font_size=14, color=(0, 0.7, 0, 1) if self.current_product.stock > 10 else (1, 0.5, 0, 1) ) )

        self.qty_input = TextInput ( hint_text="Санды киргизиңиз", multiline=False, input_filter='float', font_size=16 )
        content.add_widget ( self.qty_input )

        btn_layout = BoxLayout ( spacing=10, size_hint_y=0.3 )
        add_btn = Button ( text="➕ КОШУУ", background_color=(0.2, 0.8, 0.2, 1), bold=True )
        cancel_btn = Button ( text="❌ ЖОККО ЧЫГАРУУ", background_color=(0.8, 0.2, 0.2, 1), bold=True )

        popup = Popup ( title="Санды киргизиңиз", content=content, size_hint=(0.6, 0.5) )

        add_btn.bind ( on_press=lambda x: self.add_to_cart ( popup ) )
        cancel_btn.bind ( on_press=popup.dismiss )

        btn_layout.add_widget ( add_btn )
        btn_layout.add_widget ( cancel_btn )
        content.add_widget ( btn_layout )

        popup.open ()

    def add_to_cart(self, popup):
        try:
            quantity = float ( self.qty_input.text )
            success, message = self.sales_manager.add_to_cart ( self.current_product, quantity )
            if success:
                popup.dismiss ()
                self.update_cart_display ()
                self.search_input.text = ""
            else:
                self.show_popup ( "Ката", message )
        except ValueError:
            self.show_popup ( "Ката", "Сан туура эмес" )

    def create_cart_display(self):
        self.cart_layout = BoxLayout ( orientation='vertical', size_hint_y=0.5, spacing=5, padding=10 )

        header = BoxLayout ( size_hint_y=0.08, spacing=5 )
        header.add_widget ( Label ( text="ТОВАР", bold=True, size_hint_x=0.45, color=(0, 0, 0, 1) ) )
        header.add_widget ( Label ( text="САН", bold=True, size_hint_x=0.2, color=(0, 0, 0, 1) ) )
        header.add_widget ( Label ( text="СУММА", bold=True, size_hint_x=0.25, color=(0, 0, 0, 1) ) )
        header.add_widget ( Label ( text="", size_hint_x=0.1 ) )
        self.cart_layout.add_widget ( header )

        self.cart_scroll = ScrollView ()
        self.cart_content = BoxLayout ( orientation='vertical', size_hint_y=None, spacing=5 )
        self.cart_content.bind ( minimum_height=self.cart_content.setter ( 'height' ) )
        self.cart_scroll.add_widget ( self.cart_content )
        self.cart_layout.add_widget ( self.cart_scroll )
        self.add_widget ( self.cart_layout )

    def update_cart_display(self):
        self.cart_content.clear_widgets ()

        cart_items = self.sales_manager.get_cart_items ()
        for idx, item in enumerate ( cart_items ):
            item_box = BoxLayout ( size_hint_y=None, height=45, spacing=5 )
            with item_box.canvas.before:
                Color ( 0.95, 0.95, 0.95, 1 )
                RoundedRectangle ( size=item_box.size, pos=item_box.pos, radius=[5] )

            item_box.add_widget ( Label ( text=item['product'].name[:25], size_hint_x=0.45, font_size=12 ) )
            item_box.add_widget ( Label ( text=f"{item['quantity']:.2f} {item['product'].unit_type.value}",
                                          size_hint_x=0.2, font_size=12 ) )
            item_box.add_widget (
                Label ( text=f"{item['total']:.2f} сом", size_hint_x=0.25, font_size=12, color=(0, 0.7, 0, 1),
                        bold=True ) )

            remove_btn = Button ( text="✖", size_hint_x=0.1, background_color=(0.8, 0.2, 0.2, 1), font_size=12 )
            remove_btn.bind ( on_press=lambda x, i=idx: self.remove_from_cart ( i ) )
            item_box.add_widget ( remove_btn )

            self.cart_content.add_widget ( item_box )

        total = self.sales_manager.get_cart_total ()
        total_box = BoxLayout ( size_hint_y=None, height=50, spacing=5, padding=(0, 10, 0, 0) )
        with total_box.canvas.before:
            Color ( 0.9, 0.9, 0.9, 1 )
            RoundedRectangle ( size=total_box.size, pos=total_box.pos, radius=[5] )

        total_box.add_widget ( Label ( text="ЖАЛПЫ:", font_size=20, bold=True, size_hint_x=0.6 ) )
        total_box.add_widget (
            Label ( text=f"{total:.2f} сом", font_size=24, bold=True, color=(0, 0.8, 0, 1), size_hint_x=0.4 ) )
        self.cart_content.add_widget ( total_box )

    def remove_from_cart(self, index):
        self.sales_manager.remove_from_cart ( index )
        self.update_cart_display ()

    def create_payment_section(self):
        payment_box = BoxLayout ( size_hint_y=0.12, padding=10, spacing=10 )

        self.payment_spinner = Spinner (
            text="💵 НАКТАЛАЙ",
            values=["💵 НАКТАЛАЙ", "💳 КАРТА", "📝 НАСЫЯ"],
            size_hint_x=0.25,
            background_color=(0.9, 0.9, 0.9, 1),
            font_size=12
        )
        payment_box.add_widget ( self.payment_spinner )

        self.paid_input = TextInput (
            hint_text="Төлөм суммасы",
            multiline=False,
            input_filter='float',
            size_hint_x=0.25,
            font_size=14
        )
        payment_box.add_widget ( self.paid_input )

        complete_btn = Button ( text="✅ САТУУНУ АЯКТОО", background_color=(0.2, 0.8, 0.2, 1), font_size=12, bold=True )
        complete_btn.bind ( on_press=self.complete_sale )
        payment_box.add_widget ( complete_btn )

        clear_btn = Button ( text="🗑 КОРЗИНАНЫ ТАЗАЛОО", background_color=(0.8, 0.5, 0.2, 1), font_size=12, bold=True )
        clear_btn.bind ( on_press=self.clear_cart )
        payment_box.add_widget ( clear_btn )

        self.add_widget ( payment_box )

    def clear_cart(self, instance):
        self.sales_manager.clear_cart ()
        self.update_cart_display ()

    def complete_sale(self, instance):
        if not self.sales_manager.get_cart_items ():
            self.show_popup ( "Ката", "Корзина бош" )
            return

        payment_map = {"💵 НАКТАЛАЙ": PaymentType.CASH, "💳 КАРТА": PaymentType.CARD, "📝 НАСЫЯ": PaymentType.CREDIT}
        payment_type = payment_map[self.payment_spinner.text]

        try:
            paid_amount = float ( self.paid_input.text ) if self.paid_input.text else 0
        except ValueError:
            paid_amount = 0

        # 4 аргумент: user_id, payment_type, paid_amount, notes
        success, result = self.sales_manager.create_sale (
            self.user_data['id'],
            payment_type,
            paid_amount,
            ""
        )

        if success:
            sale_data = result
            message = f"✅ Сатуу аяктады!\n\n"
            message += f"Чек №: {sale_data['sale']['sale_number']}\n"
            message += f"Жалпы: {sale_data['sale']['total_amount']:.2f} сом\n"
            message += f"Төлөм: {sale_data['sale']['paid_amount']:.2f} сом\n"
            if sale_data['change'] > 0:
                message += f"Кайтарылды: {sale_data['change']:.2f} сом\n"
            message += f"\nСаткан товарлар:\n"
            for item in sale_data['items']:
                message += f"  • {item['product_name']} - {item['quantity']:.2f} {item['product_unit']} - {item['total']:.2f} сом\n"

            self.show_popup ( "✅ Ийгиликтүү", message )
            self.update_cart_display ()
            self.paid_input.text = ""
        else:
            self.show_popup ( "❌ Ката", result )

    def show_popup(self, title, message):
        content = BoxLayout ( orientation='vertical', spacing=10, padding=10 )
        scroll = ScrollView ( size_hint_y=0.8 )
        msg_label = Label ( text=message, font_size=12, size_hint_y=None )
        msg_label.bind ( texture_size=msg_label.setter ( 'size' ) )
        scroll.add_widget ( msg_label )
        content.add_widget ( scroll )

        btn = Button ( text="ЖАБУУ", size_hint_y=0.15, background_color=(0.3, 0.6, 0.9, 1), bold=True )
        popup = Popup ( title=title, content=content, size_hint=(0.7, 0.6) )
        btn.bind ( on_press=popup.dismiss )
        content.add_widget ( btn )
        popup.open ()











