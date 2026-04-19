from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.progressbar import ProgressBar
from kivy.uix.textinput import TextInput
from kivy.uix.image import Image
from kivy.graphics import Color, RoundedRectangle, Rectangle
from kivy.clock import Clock
from datetime import datetime, timedelta
import threading
import os


class DashboardScreen ( BoxLayout ):
    def __init__(self, user_data, product_manager, sales_manager, analytics_manager, on_navigate, **kwargs):
        super ().__init__ ( **kwargs )
        self.orientation = 'vertical'
        self.user_data = user_data
        self.product_manager = product_manager
        self.sales_manager = sales_manager
        self.analytics_manager = analytics_manager
        self.on_navigate = on_navigate

        # Иконкалардын жолдору
        self.icons_path = "assets/icons"

        # === ПРОФЕССИОНАЛДЫК ГРАДИЕНТ ФОН ===
        with self.canvas.before:
            Color ( 0.039, 0.059, 0.137, 1 )
            Rectangle ( size=self.size, pos=self.pos )
            Color ( 0.067, 0.106, 0.227, 0.8 )
            Rectangle ( size=(self.size[0], self.size[1] * 0.7), pos=self.pos )
            Color ( 0.102, 0.141, 0.322, 0.6 )
            Rectangle ( size=(self.size[0], self.size[1] * 0.5), pos=(self.pos[0], self.pos[1] + self.size[1] * 0.3) )
            Color ( 0.106, 0.09, 0.22, 0.5 )
            Rectangle ( size=(self.size[0], self.size[1] * 0.4), pos=(self.pos[0], self.pos[1]) )

        self.bind ( size=self._update_bg, pos=self._update_bg )

        self.glow_alpha = 0.3
        self.glow_direction = 0.01

        self.create_header ()
        self.create_stats_grid ()
        self.create_quick_actions ()
        self.create_info_buttons ()
        self.create_sales_period_buttons ()
        self.create_delete_all_button ()

        Clock.schedule_interval ( self.update_glow, 0.05 )
        Clock.schedule_interval ( self.update_dashboard, 10 )

    def _update_bg(self, instance, value):
        self.canvas.before.clear ()
        with self.canvas.before:
            Color ( 0.039, 0.059, 0.137, 1 )
            Rectangle ( size=self.size, pos=self.pos )
            Color ( 0.067, 0.106, 0.227, 0.8 )
            Rectangle ( size=(self.size[0], self.size[1] * 0.7), pos=self.pos )
            Color ( 0.102, 0.141, 0.322, 0.6 )
            Rectangle ( size=(self.size[0], self.size[1] * 0.5), pos=(self.pos[0], self.pos[1] + self.size[1] * 0.3) )
            Color ( 0.106, 0.09, 0.22, 0.5 )
            Rectangle ( size=(self.size[0], self.size[1] * 0.4), pos=(self.pos[0], self.pos[1]) )
            Color ( 1, 1, 1, self.glow_alpha )
            Rectangle ( size=(self.size[0], 2), pos=(self.pos[0], self.pos[1] + self.size[1] - 2) )

    def update_glow(self, dt):
        self.glow_alpha += self.glow_direction
        if self.glow_alpha >= 0.6:
            self.glow_alpha = 0.6
            self.glow_direction = -0.01
        elif self.glow_alpha <= 0.1:
            self.glow_alpha = 0.1
            self.glow_direction = 0.01
        self._update_bg ( None, None )

    def hex_to_rgb(self, hex_color):
        hex_color = hex_color.lstrip ( '#' )
        return tuple ( int ( hex_color[i:i + 2], 16 ) / 255.0 for i in (0, 2, 4) )

    def create_header(self):
        header = BoxLayout ( size_hint_y=0.11, padding=[25, 15, 25, 15], spacing=25 )

        with header.canvas.before:
            Color ( 0.15, 0.2, 0.35, 0.7 )
            RoundedRectangle ( size=header.size, pos=header.pos, radius=[25, 25, 0, 0] )
            Color ( 0, 0, 0, 0.3 )
            RoundedRectangle ( size=(header.size[0], header.size[1] + 5), pos=(header.pos[0], header.pos[1] - 3),
                               radius=[25, 25, 0, 0] )

        logo_box = BoxLayout ( size_hint_x=0.35, spacing=12 )
        logo_icon = Image ( source=os.path.join ( self.icons_path, "shop.png.png" ), size_hint_x=0.2 )
        logo_text = Label (
            text="AMAN\nSHOP",
            font_size=40,
            bold=True,
            color=(1, 1, 1, 1),
            size_hint_x=0.8
        )
        logo_box.add_widget ( logo_icon )
        logo_box.add_widget ( logo_text )
        header.add_widget ( logo_box )

        user_box = BoxLayout ( size_hint_x=0.35, spacing=12 )
        user_icon = Image ( source=os.path.join ( self.icons_path, "user.png" ), size_hint_x=0.2 )
        role_text = "АДМИНИСТРАТОР" if self.user_data['role'].value == "admin" else "КАССИР"
        user_info = Label (
            text=f"{self.user_data['full_name']}\n{role_text}",
            font_size=20,
            color=(1, 1, 1, 0.9),
            size_hint_x=0.8
        )
        user_box.add_widget ( user_icon )
        user_box.add_widget ( user_info )
        header.add_widget ( user_box )

        right_box = BoxLayout ( size_hint_x=0.3, spacing=20 )
        date_str = datetime.now ().strftime ( "%d.%m.%Y\n%H:%M" )
        date_label = Label (
            text=f"{date_str}",
            font_size=18,
            color=(1, 1, 1, 0.85),
            size_hint_x=0.55
        )
        right_box.add_widget ( date_label )

        logout_btn = Button (
            text="ЧЫГУУ",
            size_hint_x=0.45,
            background_color=(0.85, 0.25, 0.25, 1),
            background_normal='',
            font_size=18,
            bold=True
        )
        logout_btn.bind ( on_press=lambda x: self.on_navigate ( 'logout' ) )
        right_box.add_widget ( logout_btn )

        header.add_widget ( right_box )
        self.add_widget ( header )

    def create_stats_grid(self):
        self.stats_grid = GridLayout ( cols=4, size_hint_y=0.2, spacing=18, padding=[25, 15, 25, 15] )
        self.add_widget ( self.stats_grid )

        self.stat_cards = {}
        stats = [
            ("sales_count", "БҮГҮНКҮ САТУУ", "0", "#3B82F6", "#2563EB", "sales.png"),
            ("sales_total", "БҮГҮНКҮ СУММА", "0 сом", "#10B981", "#059669", "money.png"),
            ("products_count", "ТОВАРЛАР", "0", "#F59E0B", "#D97706", "produts.jpg"),
            ("low_stock", "ЖЕТИШСИЗ", "0", "#EF4444", "#DC2626", "warning.png")
        ]

        for key, title, default, color, dark_color, icon_file in stats:
            card = BoxLayout ( orientation='vertical', padding=[18, 12, 18, 12], spacing=10 )

            with card.canvas.before:
                Color ( *self.hex_to_rgb ( color ), 0.85 )
                RoundedRectangle ( size=card.size, pos=card.pos, radius=[18] )
                Color ( 0, 0, 0, 0.2 )
                RoundedRectangle ( size=(card.size[0] - 2, card.size[1] - 2), pos=(card.pos[0] + 2, card.pos[1] + 2),
                                   radius=[18] )
                Color ( 1, 1, 1, 0.15 )
                RoundedRectangle ( size=card.size, pos=card.pos, radius=[18] )

            icon = Image ( source=os.path.join ( self.icons_path, icon_file ), size_hint=(None, None), size=(48, 48),
                           pos_hint={'center_x': 0.5} )
            card.add_widget ( icon )

            title_label = Label ( text=title, font_size=16, color=(1, 1, 1, 0.85), bold=True, size_hint_y=0.3 )
            card.add_widget ( title_label )

            self.stat_cards[key] = Label ( text=default, font_size=30, bold=True, color=(1, 1, 1, 1), size_hint_y=0.3 )
            card.add_widget ( self.stat_cards[key] )

            self.stats_grid.add_widget ( card )

        Clock.schedule_once ( lambda dt: self.refresh_stats ( None ), 0.5 )

    def create_quick_actions(self):
        """НЕГИЗГИ 4 КНОПКА - ЖӨН ГАНА ТЕКСТ МЕНЕН"""
        actions = BoxLayout ( size_hint_y=0.14, padding=[25, 10, 25, 10], spacing=22 )

        buttons = [
            (" САТУУ", "sale", "#10B981", 34),
            (" ТОВАРЛАР", "products", "#3B82F6", 30),
            (" ОТЧЕТ", "reports", "#F59E0B", 30),
            (" КОЛДОНУУЧУЛАР", "users", "#8B5CF6", 26)
        ]

        for text, screen, color_hex, font_size in buttons:
            if screen == "users" and self.user_data['role'].value != "admin":
                continue

            btn = Button (
                text=text,
                font_size=font_size,
                bold=True,
                background_color=self.hex_to_rgb ( color_hex ),
                background_normal='',
                color=(1, 1, 1, 1)
            )
            btn.bind ( on_press=lambda x, s=screen: self.on_navigate ( s ) )
            actions.add_widget ( btn )

        self.add_widget ( actions )

    def create_info_buttons(self):
        """3 ИНФО КНОПКА - ЖӨН ГАНА ТЕКСТ"""
        button_layout = BoxLayout ( size_hint_y=0.1, spacing=20, padding=[25, 12, 25, 12] )

        buttons = [
            (" ЖЕТИШСИЗ ТОВАРЛАР", self.show_low_stock_list, "#F97316", 20),
            (" МӨӨНӨТҮ ӨТКӨН", self.open_expired_dialog, "#EF4444", 20),
            (" ВОЗВРАТ ТОВАРА", self.open_return_dialog, "#8B5CF6", 20)
        ]

        for text, callback, color_hex, font_size in buttons:
            btn = Button (
                text=text,
                font_size=font_size,
                bold=True,
                background_color=self.hex_to_rgb ( color_hex ),
                background_normal='',
                color=(1, 1, 1, 1)
            )
            btn.bind ( on_press=callback )
            button_layout.add_widget ( btn )

        self.add_widget ( button_layout )

    def create_sales_period_buttons(self):
        """КҮНДҮК, ЖУМАЛЫК, АЙЛЫК - ЖӨН ГАНА ТЕКСТ"""
        period_layout = BoxLayout ( size_hint_y=0.12, spacing=20, padding=[25, 15, 25, 15] )

        periods = [
            (" КҮНДҮК САТУУ", "daily", "#3B82F6", 26),
            (" ЖУМАЛЫК САТУУ", "weekly", "#3B82F6", 26),
            (" АЙЛЫК САТУУ", "monthly", "#3B82F6", 26)
        ]

        for text, period, color_hex, font_size in periods:
            btn = Button (
                text=text,
                font_size=font_size,
                bold=True,
                background_color=self.hex_to_rgb ( color_hex ),
                background_normal='',
                color=(1, 1, 1, 1)
            )
            btn.bind ( on_press=lambda x, p=period: self.show_sales_by_period ( p ) )
            period_layout.add_widget ( btn )

        self.add_widget ( period_layout )

    def create_delete_all_button(self):
        """ӨЧҮРҮҮ КНОПКАСЫ - ЖӨН ГАНА ТЕКСТ"""
        delete_layout = BoxLayout ( size_hint_y=0.07, padding=[25, 10, 25, 10], spacing=20 )
        delete_layout.add_widget ( Label ( text="", size_hint_x=0.6 ) )

        delete_btn = Button (
            text=" БАРДЫК МААЛЫМАТТАРДЫ ӨЧҮРҮҮ",
            size_hint_x=0.4,
            background_color=(0.85, 0.25, 0.25, 1),
            background_normal='',
            font_size=20,
            bold=True,
            color=(1, 1, 1, 1)
        )
        delete_btn.bind ( on_press=self.show_delete_confirmation )
        delete_layout.add_widget ( delete_btn )

        self.add_widget ( delete_layout )

    def show_sales_by_period(self, period):
        try:
            today = datetime.now ()

            if period == "daily":
                start_date = datetime ( today.year, today.month, today.day, 0, 0, 0 )
                end_date = datetime ( today.year, today.month, today.day, 23, 59, 59 )
                title = "КҮНДҮК САТУУЛАР"
                period_name = "бүгүн"
            elif period == "weekly":
                start_date = datetime ( today.year, today.month, today.day, 0, 0, 0 ) - timedelta (
                    days=today.weekday () )
                end_date = datetime ( today.year, today.month, today.day, 23, 59, 59 )
                title = "ЖУМАЛЫК САТУУЛАР"
                period_name = "жумалык"
            elif period == "monthly":
                start_date = datetime ( today.year, today.month, 1, 0, 0, 0 )
                end_date = datetime ( today.year, today.month, today.day, 23, 59, 59 )
                title = "АЙЛЫК САТУУЛАР"
                period_name = "айлык"
            else:
                return

            sales = self.sales_manager.get_sales_by_date ( start_date, end_date )

        except Exception as e:
            print ( f"Sales by period error: {e}" )
            sales = []

        content = BoxLayout ( orientation='vertical', spacing=20, padding=25 )

        with content.canvas.before:
            Color ( 0.05, 0.07, 0.15, 0.95 )
            RoundedRectangle ( size=content.size, pos=content.pos, radius=[20] )

        total_amount = sum ( s['total_amount'] for s in sales ) if sales else 0

        stats_panel = BoxLayout ( size_hint_y=0.09, spacing=25, padding=[20, 15, 20, 15] )
        with stats_panel.canvas.before:
            Color ( 0.2, 0.4, 0.6, 0.15 )
            RoundedRectangle ( size=stats_panel.size, pos=stats_panel.pos, radius=[15] )

        stats_panel.add_widget (
            Label ( text=f"{len ( sales )} сатуу", font_size=26, bold=True, color=(1, 1, 1, 0.9) ) )
        stats_panel.add_widget (
            Label ( text=f"{total_amount:,.0f} сом", font_size=26, bold=True, color=(0.3, 0.9, 0.3, 1) ) )
        content.add_widget ( stats_panel )

        scroll = ScrollView ()
        list_layout = BoxLayout ( orientation='vertical', size_hint_y=None, spacing=15 )
        list_layout.bind ( minimum_height=list_layout.setter ( 'height' ) )

        if sales:
            for sale in sales:
                sale_card = BoxLayout ( orientation='vertical', size_hint_y=None, spacing=12, padding=18 )
                items_count = min ( len ( sale['items'] ), 5 )
                sale_card.height = 120 + (items_count * 55)
                with sale_card.canvas.before:
                    Color ( 0.1, 0.12, 0.25, 0.9 )
                    RoundedRectangle ( size=sale_card.size, pos=sale_card.pos, radius=[15] )
                    Color ( 0, 0, 0, 0.3 )
                    RoundedRectangle ( size=(sale_card.size[0] - 2, sale_card.size[1] - 2),
                                       pos=(sale_card.pos[0] + 1, sale_card.pos[1] + 1), radius=[15] )

                header_box = BoxLayout ( size_hint_y=None, height=65, spacing=20 )
                sale_time = sale['created_at']
                if isinstance ( sale_time, str ):
                    sale_time = datetime.fromisoformat ( sale_time )

                date_str = sale_time.strftime ( '%d.%m.%Y' )
                time_str = sale_time.strftime ( '%H:%M' )

                header_box.add_widget (
                    Label ( text=f"{date_str}", size_hint_x=0.3, font_size=22, bold=True, color=(1, 1, 1, 0.9) ) )
                header_box.add_widget (
                    Label ( text=f"{time_str}", size_hint_x=0.25, font_size=22, bold=True, color=(1, 1, 1, 0.9) ) )
                header_box.add_widget ( Label ( text=f"{sale['total_amount']:.0f} сом", size_hint_x=0.45, font_size=26,
                                                color=(0.3, 0.9, 0.3, 1), bold=True, halign='right' ) )
                sale_card.add_widget ( header_box )

                line = BoxLayout ( size_hint_y=None, height=2 )
                with line.canvas.before:
                    Color ( 0.3, 0.4, 0.6, 0.5 )
                    RoundedRectangle ( size=line.size, pos=line.pos, radius=[0] )
                sale_card.add_widget ( line )

                for item in sale['items'][:5]:
                    item_box = BoxLayout ( size_hint_y=None, height=50, spacing=15, padding=[15, 0, 15, 0] )
                    product_name = item['product'].name if item['product'] else "Товар жок"
                    unit_value = item['product'].unit_type.value if item['product'] else "шт"
                    item_box.add_widget (
                        Label ( text=product_name, size_hint_x=0.55, font_size=19, bold=True, color=(1, 1, 1, 0.85) ) )
                    item_box.add_widget (
                        Label ( text=f"{item['quantity']:.0f} {unit_value}", size_hint_x=0.2, font_size=19,
                                halign='center', color=(1, 1, 1, 0.85) ) )
                    item_box.add_widget ( Label ( text=f"{item['total']:.0f} сом", size_hint_x=0.25, font_size=19,
                                                  color=(0.3, 0.9, 0.3, 1), halign='right', bold=True ) )
                    sale_card.add_widget ( item_box )

                if len ( sale['items'] ) > 5:
                    sale_card.add_widget (
                        Label ( text=f"... жана дагы {len ( sale['items'] ) - 5} товар", font_size=16,
                                color=(0.6, 0.6, 0.8, 1), size_hint_y=None, height=40 ) )

                list_layout.add_widget ( sale_card )
                list_layout.add_widget ( Label ( text="", size_hint_y=None, height=10 ) )
        else:
            list_layout.add_widget (
                Label ( text=f"{period_name} сатуулар жок", font_size=30, color=(0.6, 0.6, 0.8, 1), size_hint_y=None,
                        height=200, halign='center' ) )

        scroll.add_widget ( list_layout )
        content.add_widget ( scroll )

        close_btn = Button ( text="ЖАБУУ", size_hint_y=0.07, background_color=(0.3, 0.4, 0.6, 1), font_size=22,
                             bold=True )
        close_btn.bind ( on_press=lambda x: popup.dismiss () )
        content.add_widget ( close_btn )

        popup = Popup ( title=title, content=content, size_hint=(0.92, 0.88) )
        popup.open ()

    def open_return_dialog(self, instance):
        content = BoxLayout ( orientation='vertical', spacing=15, padding=25 )

        with content.canvas.before:
            Color ( 0.05, 0.07, 0.15, 0.95 )
            RoundedRectangle ( size=content.size, pos=content.pos, radius=[20] )

        title_layout = BoxLayout ( size_hint_y=None, height=60, spacing=15 )
        title_icon = Image ( source=os.path.join ( self.icons_path, "return.jpg" ), size_hint=(None, None),
                             size=(40, 40) )
        title_label = Label ( text="ВОЗВРАТ ТОВАРА", font_size=28, bold=True, color=(0.5, 0.7, 1, 1) )
        title_layout.add_widget ( title_icon )
        title_layout.add_widget ( title_label )
        content.add_widget ( title_layout )

        content.add_widget ( Label ( text="ТОВАРДЫН АТЫ:", font_size=20, bold=True, color=(1, 1, 1, 0.9) ) )
        product_input = TextInput ( hint_text="Мисалы: Нан...", multiline=False, font_size=18, size_hint_y=None,
                                    height=55 )
        content.add_widget ( product_input )

        content.add_widget ( Label ( text="КАЙТАРЫЛУУЧУ САН:", font_size=20, bold=True, color=(1, 1, 1, 0.9) ) )
        quantity_input = TextInput ( hint_text="Санды киргизиңиз", multiline=False, input_filter='float', font_size=18,
                                     size_hint_y=None, height=55 )
        content.add_widget ( quantity_input )

        content.add_widget ( Label ( text="КАЙТАРУУ СЕБЕБИ:", font_size=20, bold=True, color=(1, 1, 1, 0.9) ) )
        reason_input = TextInput ( hint_text="Мисалы: Бузулган, Жарамсыз...", multiline=False, font_size=18,
                                   size_hint_y=None, height=55 )
        content.add_widget ( reason_input )

        btn_layout = BoxLayout ( spacing=15, size_hint_y=None, height=75, padding=[0, 15, 0, 0] )

        cancel_btn = Button ( text="ЖОККО ЧЫГАРУУ", background_color=(0.8, 0.2, 0.2, 1), font_size=20, bold=True )
        confirm_btn = Button ( text="КАЙТАРУУ", background_color=(0.2, 0.7, 0.2, 1), font_size=20, bold=True )

        popup = Popup ( title="ВОЗВРАТ ТОВАРА", content=content, size_hint=(0.65, 0.65) )

        def do_return(instance):
            product_name = product_input.text.strip ()
            quantity = quantity_input.text.strip ()
            reason = reason_input.text.strip ()

            if not product_name or not quantity:
                self.show_message ( "Ката", "Товар аты жана санды толтуруңуз" )
                return

            try:
                quantity_val = float ( quantity )
            except ValueError:
                self.show_message ( "Ката", "Сан туура эмес" )
                return

            products = self.product_manager.search_products ( product_name )
            if not products:
                self.show_message ( "Ката", f"'{product_name}' товары табылган жок" )
                return

            product = products[0]

            if product.stock < quantity_val:
                self.show_message ( "Ката",
                                    f"Складда жетишсиз! {product.name} - {product.stock} {product.unit_type.value}" )
                return

            success, result = self.product_manager.update_stock ( product.id, -quantity_val )

            if success:
                popup.dismiss ()
                product_input.text = ""
                quantity_input.text = ""
                reason_input.text = ""
                self.refresh_stats ( None )
                self.show_message ( "Ийгиликтүү", f"{product.name} - {quantity_val} даана кайтарылды" )
            else:
                self.show_message ( "Ката", result )

        confirm_btn.bind ( on_press=do_return )
        cancel_btn.bind ( on_press=popup.dismiss )

        btn_layout.add_widget ( cancel_btn )
        btn_layout.add_widget ( confirm_btn )
        content.add_widget ( btn_layout )

        popup.open ()

    def open_expired_dialog(self, instance):
        content = BoxLayout ( orientation='vertical', spacing=15, padding=25 )

        with content.canvas.before:
            Color ( 0.05, 0.07, 0.15, 0.95 )
            RoundedRectangle ( size=content.size, pos=content.pos, radius=[20] )

        title_layout = BoxLayout ( size_hint_y=None, height=60, spacing=15 )
        title_icon = Image ( source=os.path.join ( self.icons_path, "warning.jpg" ), size_hint=(None, None),
                             size=(40, 40) )
        title_label = Label ( text="МӨӨНӨТҮ ӨТКӨН ТОВАР", font_size=28, bold=True, color=(1, 0.5, 0.5, 1) )
        title_layout.add_widget ( title_icon )
        title_layout.add_widget ( title_label )
        content.add_widget ( title_layout )

        content.add_widget ( Label ( text="ТОВАРДЫН АТЫ:", font_size=20, bold=True, color=(1, 1, 1, 0.9) ) )
        product_input = TextInput ( hint_text="Мисалы: Нан, Сүт...", multiline=False, font_size=18, size_hint_y=None,
                                    height=55 )
        content.add_widget ( product_input )

        content.add_widget ( Label ( text="МӨӨНӨТҮ ӨТКӨН ДАТА:", font_size=20, bold=True, color=(1, 1, 1, 0.9) ) )
        date_input = TextInput ( hint_text="DD-MM-YYYY", multiline=False, font_size=20, size_hint_y=None, height=55 )
        content.add_widget ( date_input )

        content.add_widget ( Label ( text="САНЫ:", font_size=20, bold=True, color=(1, 1, 1, 0.9) ) )
        quantity_input = TextInput ( hint_text="Санды киргизиңиз", multiline=False, input_filter='float', font_size=20,
                                     size_hint_y=None, height=55 )
        content.add_widget ( quantity_input )

        content.add_widget ( Label ( text="ЭСКЕРТҮҮ:", font_size=20, bold=True, color=(1, 1, 1, 0.9) ) )
        notes_input = TextInput ( hint_text="Кошумча маалымат", multiline=False, font_size=18, size_hint_y=None,
                                  height=55 )
        content.add_widget ( notes_input )

        btn_layout = BoxLayout ( spacing=15, size_hint_y=None, height=75, padding=[0, 15, 0, 0] )

        cancel_btn = Button ( text="ЖОККО ЧЫГАРУУ", background_color=(0.8, 0.2, 0.2, 1), font_size=20, bold=True )
        confirm_btn = Button ( text="КОШУУ", background_color=(0.2, 0.7, 0.2, 1), font_size=20, bold=True )

        popup = Popup ( title="ПРОСРОЧКА ТОВАР", content=content, size_hint=(0.65, 0.7) )

        def do_add(instance):
            product_name = product_input.text.strip ()
            date_str = date_input.text.strip ()
            quantity = quantity_input.text.strip ()
            notes = notes_input.text.strip ()

            if not product_name or not date_str or not quantity:
                self.show_message ( "Ката", "Толук толтуруңуз" )
                return

            try:
                quantity_val = float ( quantity )
                expiry_date = datetime.strptime ( date_str, "%Y-%m-%d" )
            except ValueError:
                self.show_message ( "Ката", "Дата же сан туура эмес" )
                return

            products = self.product_manager.search_products ( product_name )
            if not products:
                self.show_message ( "Ката", f"'{product_name}' товары табылган жок" )
                return

            product = products[0]

            if product.stock < quantity_val:
                self.show_message ( "Ката",
                                    f"Складда жетишсиз! {product.name} - {product.stock} {product.unit_type.value}" )
                return

            success, result = self.product_manager.update_stock ( product.id, -quantity_val )

            if success:
                popup.dismiss ()
                product_input.text = ""
                date_input.text = ""
                quantity_input.text = ""
                notes_input.text = ""
                self.refresh_stats ( None )
                self.show_message ( "Ийгиликтүү", f"{product.name} - {quantity_val} даана просрочкага кошулду" )
            else:
                self.show_message ( "Ката", result )

        confirm_btn.bind ( on_press=do_add )
        cancel_btn.bind ( on_press=popup.dismiss )

        btn_layout.add_widget ( cancel_btn )
        btn_layout.add_widget ( confirm_btn )
        content.add_widget ( btn_layout )

        popup.open ()

    def show_low_stock_list(self, instance):
        try:
            low_stock = self.product_manager.get_low_stock_products ()
        except:
            low_stock = []

        content = BoxLayout ( orientation='vertical', spacing=20, padding=25 )

        with content.canvas.before:
            Color ( 0.05, 0.07, 0.15, 0.95 )
            RoundedRectangle ( size=content.size, pos=content.pos, radius=[20] )

        stats_panel = BoxLayout ( size_hint_y=0.09, spacing=25, padding=[20, 12, 20, 12] )
        with stats_panel.canvas.before:
            Color ( 0.8, 0.3, 0.1, 0.15 )
            RoundedRectangle ( size=stats_panel.size, pos=stats_panel.pos, radius=[15] )

        stats_panel.add_widget (
            Label ( text=f"Жалпы: {len ( low_stock )} товар", font_size=24, bold=True, color=(1, 1, 1, 0.9) ) )
        stats_panel.add_widget (
            Label ( text=f"Түгөнгөн: {len ( [p for p in low_stock if p.stock == 0] )}", font_size=22,
                    color=(1, 0.4, 0.4, 1) ) )
        stats_panel.add_widget (
            Label ( text=f"Аз калган: {len ( [p for p in low_stock if p.stock > 0] )}", font_size=22,
                    color=(1, 0.7, 0.2, 1) ) )
        content.add_widget ( stats_panel )

        scroll = ScrollView ()
        list_layout = BoxLayout ( orientation='vertical', size_hint_y=None, spacing=15 )
        list_layout.bind ( minimum_height=list_layout.setter ( 'height' ) )

        if low_stock:
            out_of_stock = [p for p in low_stock if p.stock == 0]
            if out_of_stock:
                title_layout = BoxLayout ( size_hint_y=None, height=65, spacing=10 )
                title_icon = Image ( source=os.path.join ( self.icons_path, "warning.jpg" ), size_hint=(None, None),
                                     size=(30, 30) )
                title_label = Label ( text="ТҮГӨНГӨН ТОВАРЛАР:", font_size=28, bold=True, color=(1, 0.4, 0.4, 1) )
                title_layout.add_widget ( title_icon )
                title_layout.add_widget ( title_label )
                list_layout.add_widget ( title_layout )

                for p in out_of_stock:
                    item = BoxLayout ( size_hint_y=None, height=75, spacing=20, padding=[20, 12, 20, 12] )
                    with item.canvas.before:
                        Color ( 0.15, 0.08, 0.08, 0.8 )
                        RoundedRectangle ( size=item.size, pos=item.pos, radius=[12] )

                    item_icon = Image ( source=os.path.join ( self.icons_path, "warning.png" ), size_hint=(None, None),
                                        size=(30, 30) )
                    item.add_widget ( item_icon )
                    item.add_widget (
                        Label ( text=p.name, size_hint_x=0.65, font_size=22, bold=True, color=(1, 1, 1, 0.9) ) )
                    item.add_widget ( Label ( text=f"Склад: 0 {p.unit_type.value}", size_hint_x=0.25, font_size=20,
                                              color=(1, 0.4, 0.4, 1), bold=True ) )
                    list_layout.add_widget ( item )

            low = [p for p in low_stock if p.stock > 0]
            if low:
                if out_of_stock:
                    list_layout.add_widget ( Label ( text="", size_hint_y=None, height=15 ) )
                    title_layout = BoxLayout ( size_hint_y=None, height=65, spacing=10 )
                    title_icon = Image ( source=os.path.join ( self.icons_path, "warning.png" ), size_hint=(None, None),
                                         size=(30, 30) )
                    title_label = Label ( text="АЗ КАЛГАН ТОВАРЛАР:", font_size=28, bold=True, color=(1, 0.7, 0.2, 1) )
                    title_layout.add_widget ( title_icon )
                    title_layout.add_widget ( title_label )
                    list_layout.add_widget ( title_layout )

                for p in low:
                    item = BoxLayout ( size_hint_y=None, height=75, spacing=20, padding=[20, 12, 20, 12] )
                    with item.canvas.before:
                        Color ( 0.15, 0.12, 0.08, 0.8 )
                        RoundedRectangle ( size=item.size, pos=item.pos, radius=[12] )

                    item_icon = Image ( source=os.path.join ( self.icons_path, "warning.png" ), size_hint=(None, None),
                                        size=(30, 30) )
                    item.add_widget ( item_icon )
                    item.add_widget (
                        Label ( text=p.name, size_hint_x=0.65, font_size=22, bold=True, color=(1, 1, 1, 0.9) ) )
                    item.add_widget (
                        Label ( text=f"Склад: {p.stock} {p.unit_type.value}", size_hint_x=0.25, font_size=20,
                                color=(1, 0.7, 0.2, 1), bold=True ) )
                    list_layout.add_widget ( item )
        else:
            success_layout = BoxLayout ( size_hint_y=None, height=150, spacing=10 )
            success_icon = Image ( source=os.path.join ( self.icons_path, "shop.png.png" ), size_hint=(None, None),
                                   size=(50, 50) )
            success_label = Label ( text="БАРДЫК ТОВАРЛАР ЖЕТИШТҮҮ!", font_size=30, color=(0.3, 0.9, 0.3, 1) )
            success_layout.add_widget ( success_icon )
            success_layout.add_widget ( success_label )
            list_layout.add_widget ( success_layout )

        scroll.add_widget ( list_layout )
        content.add_widget ( scroll )

        close_btn = Button ( text="ЖАБУУ", size_hint_y=0.07, background_color=(0.3, 0.4, 0.6, 1), font_size=24,
                             bold=True )
        close_btn.bind ( on_press=lambda x: popup.dismiss () )
        content.add_widget ( close_btn )

        popup = Popup ( title="ЖЕТИШСИЗ ТОВАРЛАР", content=content, size_hint=(0.88, 0.82) )
        popup.open ()

    def show_delete_confirmation(self, instance):
        content = BoxLayout ( orientation='vertical', spacing=15, padding=25 )

        with content.canvas.before:
            Color ( 0.05, 0.07, 0.15, 0.95 )
            RoundedRectangle ( size=content.size, pos=content.pos, radius=[20] )

        warning_text = (
            "КАТУУ ЭСКЕРТҮҮ!\n\n"
            "Бул иш-аракет ТОЛУК КАЙТАРЫЛГЫС!\n\n"
            "Төмөнкү бардык маалыматтар ТОЛУГУ МЕНЕН өчүрүлөт:\n\n"
            "• Бардык сатуулар\n"
            "• Бардык товарлар\n"
            "• Бардык колдонуучулар (админден башка)\n"
            "• Бардык отчеттор\n"
            "• Бардык чектер\n\n"
            "Сиз чын эле бардык маалыматтарды өчүрүүнү каалайсызбы?"
        )

        warning_label = Label ( text=warning_text, font_size=16, color=(1, 0.4, 0.4, 1), size_hint_y=None )
        warning_label.bind ( texture_size=warning_label.setter ( 'size' ) )
        content.add_widget ( warning_label )

        content.add_widget (
            Label ( text="Тастыктоо үчүн администратордун сырсөзүн киргизиңиз:", font_size=16, color=(1, 1, 1, 0.8),
                    size_hint_y=None, height=35 ) )

        self.delete_password_input = TextInput (
            hint_text="Администратордун сырсөзү",
            password=True,
            multiline=False,
            font_size=18,
            size_hint_y=None,
            height=55
        )
        content.add_widget ( self.delete_password_input )

        btn_layout = BoxLayout ( spacing=15, size_hint_y=None, height=70 )

        cancel_btn = Button ( text="ЖОК, ЖОККО ЧЫГАРУУ", background_color=(0.5, 0.5, 0.5, 1), font_size=18, bold=True )
        confirm_btn = Button ( text="ООБА, БААРЫН ӨЧҮРҮҮ", background_color=(0.8, 0.2, 0.2, 1), font_size=18,
                               bold=True )

        btn_layout.add_widget ( cancel_btn )
        btn_layout.add_widget ( confirm_btn )
        content.add_widget ( btn_layout )

        popup = Popup ( title="БАРДЫК МААЛЫМАТТАРДЫ ӨЧҮРҮҮ", content=content, size_hint=(0.7, 0.6) )
        cancel_btn.bind ( on_press=popup.dismiss )
        confirm_btn.bind ( on_press=lambda x: self.delete_all_data ( popup ) )
        popup.open ()

    def delete_all_data(self, popup):
        password = self.delete_password_input.text

        if password != "admin123":
            error_content = BoxLayout ( orientation='vertical', spacing=15, padding=30 )
            error_content.add_widget ( Label ( text="Сырсөз туура эмес!", font_size=18 ) )
            error_popup = Popup ( title="Ката", content=error_content, size_hint=(0.4, 0.2) )
            error_popup.open ()
            return

        popup.dismiss ()

        progress_content = BoxLayout ( orientation='vertical', spacing=15, padding=30 )
        progress_content.add_widget ( Label ( text="Маалыматтар өчүрүлүүдө...", font_size=20 ) )
        progress_bar = ProgressBar ( max=100, value=0, size_hint_y=None, height=30 )
        progress_content.add_widget ( progress_bar )

        progress_popup = Popup ( title="Өчүрүү", content=progress_content, size_hint=(0.5, 0.28), auto_dismiss=False )
        progress_popup.open ()

        def delete():
            import time
            from database.db_manager import DatabaseManager
            from database.models import Sale, SaleItem, Product, Category, User

            try:
                db = DatabaseManager ()
                session = db.get_session ()

                session.query ( SaleItem ).delete ()
                progress_bar.value = 20
                time.sleep ( 0.2 )
                session.commit ()

                session.query ( Sale ).delete ()
                progress_bar.value = 40
                time.sleep ( 0.2 )
                session.commit ()

                session.query ( Product ).delete ()
                progress_bar.value = 60
                time.sleep ( 0.2 )
                session.commit ()

                session.query ( Category ).delete ()
                progress_bar.value = 75
                time.sleep ( 0.2 )
                session.commit ()

                users = session.query ( User ).filter ( User.username != "admin" ).all ()
                for user in users:
                    session.delete ( user )
                progress_bar.value = 85
                time.sleep ( 0.2 )
                session.commit ()

                session.close ()

                for folder in ["reports", "receipts", "logs"]:
                    if os.path.exists ( folder ):
                        for f in os.listdir ( folder ):
                            f_path = os.path.join ( folder, f )
                            if os.path.isfile ( f_path ):
                                try:
                                    os.remove ( f_path )
                                except:
                                    pass
                progress_bar.value = 100
                time.sleep ( 0.5 )

                Clock.schedule_once ( lambda dt: self.delete_complete ( progress_popup ), 0 )

            except Exception as error:
                print ( f"Delete error: {error}" )
                Clock.schedule_once ( lambda dt: self.delete_error ( progress_popup, str ( error ) ), 0 )

        threading.Thread ( target=delete, daemon=True ).start ()

    def delete_complete(self, progress_popup):
        progress_popup.dismiss ()
        self.refresh_stats ( None )

        success_content = BoxLayout ( orientation='vertical', spacing=15, padding=30 )
        success_content.add_widget (
            Label ( text="БАРДЫК МААЛЫМАТТАР ИЙГИЛИКТҮҮ ӨЧҮРҮЛДҮ!", font_size=20, color=(0.3, 0.9, 0.3, 1) ) )
        success_content.add_widget ( Label ( text="Дашборд жаңыртылды", font_size=16, color=(1, 1, 1, 0.7) ) )

        close_btn = Button ( text="ЖАБУУ", size_hint_y=0.22, background_color=(0.3, 0.5, 0.8, 1), font_size=18 )
        success_content.add_widget ( close_btn )

        success_popup = Popup ( title="Ийгиликтүү", content=success_content, size_hint=(0.5, 0.28) )
        close_btn.bind ( on_press=success_popup.dismiss )
        success_popup.open ()

    def delete_error(self, progress_popup, error_msg):
        progress_popup.dismiss ()

        error_content = BoxLayout ( orientation='vertical', spacing=15, padding=30 )
        error_content.add_widget ( Label ( text=f"Ката: {error_msg}", font_size=16, color=(1, 0.3, 0.3, 1) ) )
        error_content.add_widget (
            Label ( text="Кээ бир маалыматтар өчүрүлбөй калышы мүмкүн.", font_size=14, color=(1, 1, 1, 0.7) ) )

        close_btn = Button ( text="ЖАБУУ", size_hint_y=0.22, background_color=(0.5, 0.5, 0.5, 1), font_size=18 )
        error_content.add_widget ( close_btn )

        error_popup = Popup ( title="Ката", content=error_content, size_hint=(0.5, 0.28) )
        close_btn.bind ( on_press=error_popup.dismiss )
        error_popup.open ()

    def refresh_stats(self, instance):
        try:
            today = datetime.now ().date ()
            sales = self.sales_manager.get_today_sales ()
            total_today = sum ( s['total_amount'] for s in sales ) if sales else 0
            total_products = len ( self.product_manager.get_all_products () )
            low_stock = len ( self.product_manager.get_low_stock_products () )

            self.stat_cards['sales_count'].text = f"{len ( sales )}"
            self.stat_cards['sales_total'].text = f"{total_today:.0f} сом"
            self.stat_cards['products_count'].text = f"{total_products}"
            self.stat_cards['low_stock'].text = f"{low_stock}"

        except Exception as e:
            print ( f"Refresh stats error: {e}" )

    def update_dashboard(self, dt):
        self.refresh_stats ( None )

    def show_message(self, title, message):
        content = BoxLayout ( orientation='vertical', spacing=15, padding=30 )

        with content.canvas.before:
            Color ( 0.05, 0.07, 0.15, 0.95 )
            RoundedRectangle ( size=content.size, pos=content.pos, radius=[20] )

        content.add_widget ( Label ( text=message, font_size=18, color=(1, 1, 1, 0.9) ) )
        btn = Button ( text="ЖАБУУ", size_hint_y=0.22, background_color=(0.3, 0.5, 0.8, 1), font_size=18, bold=True )
        popup = Popup ( title=title, content=content, size_hint=(0.45, 0.25) )
        btn.bind ( on_press=popup.dismiss )
        content.add_widget ( btn )
        popup.open ()