from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner
from kivy.graphics import Color, RoundedRectangle, Rectangle
from kivy.core.window import Window
from kivy.clock import Clock

from database.models import UnitType


class ProductScreen ( BoxLayout ):
    def __init__(self, user_data, product_manager, on_back, **kwargs):
        super ().__init__ ( **kwargs )
        self.orientation = 'vertical'
        self.user_data = user_data
        self.product_manager = product_manager
        self.on_back = on_back
        self.show_archive = False
        self.search_timer = None

        # Түс схемасы
        self.colors = {
            'primary': (0.2, 0.5, 0.8, 1),  # Негизги көк
            'success': (0.2, 0.7, 0.3, 1),  # Жашыл
            'danger': (0.8, 0.2, 0.2, 1),  # Кызыл
            'warning': (0.9, 0.6, 0.1, 1),  # Сары
            'dark': (0.2, 0.2, 0.2, 1),  # Кара
            'gray': (0.4, 0.4, 0.4, 1),  # Боз
            'light': (0.95, 0.95, 0.95, 1),  # Ачык
            'white': (1, 1, 1, 1),  # Ак
            'header': (0.15, 0.35, 0.6, 1),  # Башчы түсү
        }

        self.create_header ()
        self.create_stats_bar ()
        self.create_product_list ()
        self.create_add_button ()

        self.load_products ()

    def create_header(self):
        """Башкы панель - профессионалдуу дизайн"""
        header = BoxLayout ( size_hint_y=0.09, padding=[15, 5, 15, 5], spacing=15 )

        with header.canvas.before:
            Color ( *self.colors['header'] )
            Rectangle ( size=header.size, pos=header.pos )

        # Артка кнопкасы
        back_btn = Button (
            text="←",
            size_hint_x=0.08,
            background_color=self.colors['gray'],
            background_normal='',
            color=self.colors['white'],
            font_size=28,
            bold=True
        )
        back_btn.bind ( on_press=lambda x: self.on_back () )
        header.add_widget ( back_btn )

        # Башкы аталыш
        title = Label (
            text="📦 ТОВАРЛАРДЫ БАШКАРУУ",
            color=self.colors['white'],
            font_size=24,
            bold=True,
            size_hint_x=0.35
        )
        header.add_widget ( title )

        # Издөө талаасы - стилдүү
        search_box = BoxLayout ( size_hint_x=0.35, spacing=5 )
        self.search_input = TextInput (
            hint_text="🔍 Товар изде...",
            multiline=False,
            font_size=18,
            size_hint_x=0.9,
            background_color=(1, 1, 1, 0.95),
            foreground_color=self.colors['dark'],
            cursor_color=self.colors['primary'],
            padding=[15, 12, 15, 12]
        )
        self.search_input.bind ( text=self.on_search_delayed )
        search_box.add_widget ( self.search_input )

        # Издөө баскычы
        search_btn = Button (
            text="🔍",
            size_hint_x=0.1,
            background_color=self.colors['primary'],
            background_normal='',
            color=self.colors['white'],
            font_size=18,
            bold=True
        )
        search_btn.bind ( on_press=lambda x: self.search_products () )
        search_box.add_widget ( search_btn )
        header.add_widget ( search_box )

        # Архив кнопкасы
        self.archive_btn = Button (
            text="📦 Архив",
            size_hint_x=0.12,
            background_color=self.colors['gray'],
            background_normal='',
            color=self.colors['white'],
            font_size=20,
            bold=True
        )
        self.archive_btn.bind ( on_press=self.toggle_archive )
        header.add_widget ( self.archive_btn )

        # Жаңыртуу кнопкасы
        refresh_btn = Button (
            text="🔄",
            size_hint_x=0.08,
            background_color=self.colors['primary'],
            background_normal='',
            color=self.colors['white'],
            font_size=18,
            bold=True
        )
        refresh_btn.bind ( on_press=lambda x: self.load_products () )
        header.add_widget ( refresh_btn )

        self.add_widget ( header )

    def create_stats_bar(self):
        """Статистика панели"""
        stats_bar = BoxLayout ( size_hint_y=0.07, padding=[15, 5, 15, 5], spacing=20 )

        with stats_bar.canvas.before:
            Color ( 0.98, 0.98, 0.98, 1 )
            Rectangle ( size=stats_bar.size, pos=stats_bar.pos )

        # Товарлардын саны
        self.stats_label = Label (
            text="📊 Жүктөлүүдө...",
            color=self.colors['gray'],
            font_size=30,
            size_hint_x=0.5,
            halign='left',
            valign='middle'
        )
        self.stats_label.bind ( size=self.stats_label.setter ( 'text_size' ) )
        stats_bar.add_widget ( self.stats_label )

        # Тез фильтрлер
        filter_box = BoxLayout ( size_hint_x=0.5, spacing=10 )

        self.all_btn = Button (
            text="Бардык",
            size_hint_x=0.33,
            background_color=self.colors['primary'],
            background_normal='',
            color=self.colors['white'],
            font_size=18,
            bold=True
        )
        self.all_btn.bind ( on_press=lambda x: self.set_filter ( 'all' ) )
        filter_box.add_widget ( self.all_btn )

        self.active_btn = Button (
            text="Активдүү",
            size_hint_x=0.33,
            background_color=self.colors['success'],
            background_normal='',
            color=self.colors['white'],
            font_size=18,
            bold=True
        )
        self.active_btn.bind ( on_press=lambda x: self.set_filter ( 'active' ) )
        filter_box.add_widget ( self.active_btn )

        self.archived_btn = Button (
            text="Архив",
            size_hint_x=0.33,
            background_color=self.colors['gray'],
            background_normal='',
            color=self.colors['white'],
            font_size=18,
            bold=True
        )
        self.archived_btn.bind ( on_press=lambda x: self.set_filter ( 'archived' ) )
        filter_box.add_widget ( self.archived_btn )

        stats_bar.add_widget ( filter_box )
        self.add_widget ( stats_bar )

    def create_product_list(self):
        """Товарлар тизмеси - карточкалар менен"""
        self.product_layout = BoxLayout ( orientation='vertical', spacing=10, padding=[10, 5, 10, 5] )
        self.scroll = ScrollView (
            bar_width=10,
            bar_color=self.colors['primary'],
            bar_inactive_color=self.colors['gray']
        )
        self.product_grid = GridLayout ( cols=1, size_hint_y=None, spacing=10, padding=[5, 5, 5, 5] )
        self.product_grid.bind ( minimum_height=self.product_grid.setter ( 'height' ) )
        self.scroll.add_widget ( self.product_grid )
        self.product_layout.add_widget ( self.scroll )
        self.add_widget ( self.product_layout )

    def create_add_button(self):
        """Товар кошуу кнопкасы - стилдүү"""
        add_btn = Button (
            text="➕ ЖАҢЫ ТОВАР КОШУУ",
            size_hint_y=0.08,
            background_color=self.colors['success'],
            background_normal='',
            color=self.colors['white'],
            font_size=25,
            bold=True,
            padding=[10, 10, 10, 10]
        )
        add_btn.bind ( on_press=self.show_add_product_dialog )
        self.add_widget ( add_btn )

    def on_search_delayed(self, instance, value):
        """Кечиктирилген издөө (дебонсинг)"""
        if self.search_timer:
            self.search_timer.cancel ()
        self.search_timer = Clock.schedule_once ( lambda dt: self.search_products (), 0.5 )

    def search_products(self):
        """Товарларды издөө"""
        self.load_products ( self.search_input.text.strip () )

    def set_filter(self, filter_type):
        """Фильтрди өзгөртүү"""
        if filter_type == 'all':
            self.show_archive = False
            self.all_btn.background_color = self.colors['primary']
            self.active_btn.background_color = self.colors['success']
            self.archived_btn.background_color = self.colors['gray']
            self.archive_btn.text = "📦 Архив"
            self.archive_btn.background_color = self.colors['gray']
            self.load_products ()
        elif filter_type == 'active':
            self.show_archive = False
            self.all_btn.background_color = self.colors['gray']
            self.active_btn.background_color = self.colors['success']
            self.archived_btn.background_color = self.colors['gray']
            self.archive_btn.text = "📦 Архив"
            self.archive_btn.background_color = self.colors['gray']
            self.load_products ()
        elif filter_type == 'archived':
            self.show_archive = True
            self.all_btn.background_color = self.colors['gray']
            self.active_btn.background_color = self.colors['gray']
            self.archived_btn.background_color = self.colors['warning']
            self.archive_btn.text = "📂 Активдүү"
            self.archive_btn.background_color = self.colors['success']
            self.load_products ()

    def toggle_archive(self, instance):
        """Архивди көрсөтүү/жашыруу"""
        if self.show_archive:
            self.show_archive = False
            self.archive_btn.text = "📦 Архив"
            self.archive_btn.background_color = self.colors['gray']
            self.all_btn.background_color = self.colors['primary']
            self.active_btn.background_color = self.colors['success']
            self.archived_btn.background_color = self.colors['gray']
        else:
            self.show_archive = True
            self.archive_btn.text = "📂 Активдүү"
            self.archive_btn.background_color = self.colors['success']
            self.all_btn.background_color = self.colors['gray']
            self.active_btn.background_color = self.colors['gray']
            self.archived_btn.background_color = self.colors['warning']
        self.load_products ()

    def load_products(self, search_text=""):
        """Товарларды жүктөө"""
        try:
            if search_text:
                products = self.product_manager.search_products ( search_text )
            else:
                if self.show_archive:
                    products = self.product_manager.get_archived_products ()
                else:
                    products = self.product_manager.get_all_products ()

            self.product_grid.clear_widgets ()

            if not products:
                no_products = BoxLayout ( orientation='vertical', size_hint_y=None, height=300, spacing=20 )
                with no_products.canvas.before:
                    Color ( 0.98, 0.98, 0.98, 1 )
                    RoundedRectangle ( size=no_products.size, pos=no_products.pos, radius=[15] )

                icon = Label ( text="📭", font_size=64, color=self.colors['gray'] )
                no_products.add_widget ( icon )

                msg = "Товар табылган жок" if search_text else "Товарлар тизмеси бош"
                label = Label ( text=msg, font_size=18, color=self.colors['gray'] )
                no_products.add_widget ( label )

                if not search_text and not self.show_archive:
                    hint = Button (
                        text="➕ Биринчи товарды кошуу",
                        size_hint_y=0.3,
                        size_hint_x=0.5,
                        pos_hint={'center_x': 0.5},
                        background_color=self.colors['primary'],
                        background_normal='',
                        color=self.colors['white']
                    )
                    hint.bind ( on_press=self.show_add_product_dialog )
                    no_products.add_widget ( hint )

                self.product_grid.add_widget ( no_products )
            else:
                for product in products:
                    self.add_product_card ( product )

            # Статистиканы жаңыртуу
            total_products = len ( self.product_manager.get_all_products () )
            archived_products = len ( self.product_manager.get_archived_products () )
            self.stats_label.text = f"📊 Жалпы: {total_products} | Архив: {archived_products} | Көрсөтүлүүдө: {len ( products )}"

        except Exception as e:
            print ( f"Load products error: {e}" )

    def add_product_card(self, product):
        """Профессионалдуу товар карточкасы"""
        card = BoxLayout (
            size_hint_y=None,
            height=120,
            spacing=15,
            padding=[15, 10, 15, 10]
        )

        with card.canvas.before:
            Color ( 1, 1, 1, 1 )
            RoundedRectangle ( size=card.size, pos=card.pos, radius=[12] )
            Color ( 0.9, 0.9, 0.9, 1 )
            RoundedRectangle ( size=(card.width, 1), pos=(card.x, card.y), radius=[0] )

        # Статус индикатору
        status_indicator = BoxLayout ( size_hint_x=0.02, spacing=0 )
        with status_indicator.canvas:
            Color ( *self.colors['success'] if product.is_active else self.colors['warning'] )
            RoundedRectangle ( size=status_indicator.size, pos=status_indicator.pos, radius=[6, 0, 0, 6] )
        card.add_widget ( status_indicator )

        # Товар маалыматы
        info = BoxLayout ( orientation='vertical', size_hint_x=0.55, spacing=5 )

        # Аталышы жана ID
        name_row = BoxLayout ( size_hint_y=0.35, spacing=10 )
        name_label = Label (
            text=product.name,
            font_size=40,
            bold=True,
            color=self.colors['dark'],
            halign='left',
            valign='middle',
            size_hint_x=0.8
        )
        name_label.bind ( size=name_label.setter ( 'text_size' ) )
        name_row.add_widget ( name_label )

        id_label = Label (
            text=f"ID: {product.id}",
            font_size=15,
            color=self.colors['gray'],
            halign='right',
            valign='middle',
            size_hint_x=0.2
        )
        id_label.bind ( size=id_label.setter ( 'text_size' ) )
        name_row.add_widget ( id_label )
        info.add_widget ( name_row )

        # Баасы, саны, категория
        details = BoxLayout ( size_hint_y=0.35, spacing=15 )

        price_box = BoxLayout ( size_hint_x=0.35, spacing=5 )
        price_icon = Label ( text="💰", font_size=14, size_hint_x=0.2 )
        price_label = Label (
            text=f"{product.price:,.0f} сом",
            font_size=20,
            color=self.colors['primary'],
            bold=True,
            halign='left'
        )
        price_box.add_widget ( price_icon )
        price_box.add_widget ( price_label )
        details.add_widget ( price_box )

        stock_box = BoxLayout ( size_hint_x=0.35, spacing=5 )
        stock_icon = Label ( text="📦", font_size=10, size_hint_x=0.2 )
        stock_color = self.colors['success'] if product.stock > 10 else (
            self.colors['warning'] if product.stock > 0 else self.colors['danger'])
        stock_label = Label (
            text=f"{product.stock:,.0f} {product.unit_type.value}",
            font_size=30,
            color=stock_color,
            bold=True,
            halign='left'
        )
        stock_box.add_widget ( stock_icon )
        stock_box.add_widget ( stock_label )
        details.add_widget ( stock_box )

        cat_box = BoxLayout ( size_hint_x=0.3, spacing=5 )
        cat_icon = Label ( text="🏷️", font_size=14, size_hint_x=0.2 )
        cat_name = product.category.name if product.category else "Категория жок"
        cat_label = Label (
            text=cat_name,
            font_size=30,
            color=self.colors['gray'],
            halign='left'
        )
        cat_box.add_widget ( cat_icon )
        cat_box.add_widget ( cat_label )
        details.add_widget ( cat_box )

        info.add_widget ( details )

        # Штрихкод (бар болсо)
        if product.barcode:
            barcode = Label (
                text=f"🔖 {product.barcode}",
                font_size=11,
                color=self.colors['gray'],
                halign='left',
                size_hint_y=0.3
            )
            barcode.bind ( size=barcode.setter ( 'text_size' ) )
            info.add_widget ( barcode )

        card.add_widget ( info )

        # Башкаруу кнопкалары
        buttons = BoxLayout ( size_hint_x=0.43, spacing=8 )

        # Түзөтүү
        edit_btn = Button (
            text=" Түзөтүү",
            background_color=self.colors['primary'],
            background_normal='',
            color=self.colors['white'],
            font_size=25,
            bold=True
        )
        edit_btn.bind ( on_press=lambda x, p=product: self.show_edit_product_dialog ( p ) )
        buttons.add_widget ( edit_btn )

        # Складды жаңыртуу
        stock_btn = Button (
            text=" Склад",
            background_color=self.colors['success'],
            background_normal='',
            color=self.colors['white'],
            font_size=25,
            bold=True
        )
        stock_btn.bind ( on_press=lambda x, p=product: self.update_stock ( p ) )
        buttons.add_widget ( stock_btn )

        # Архив/Калыбына келтирүү
        if product.is_active:
            archive_btn = Button (
                text=" Архивге",
                background_color=self.colors['warning'],
                background_normal='',
                color=self.colors['white'],
                font_size=25,
                bold=True
            )
            archive_btn.bind ( on_press=lambda x, p=product: self.archive_product ( p ) )
            buttons.add_widget ( archive_btn )
        else:
            restore_btn = Button (
                text=" Калыбына",
                background_color=self.colors['success'],
                background_normal='',
                color=self.colors['white'],
                font_size=25,
                bold=True
            )
            restore_btn.bind ( on_press=lambda x, p=product: self.restore_product ( p ) )
            buttons.add_widget ( restore_btn )

        # Өчүрүү
        delete_btn = Button (
            text=" Өчүрүү",
            background_color=self.colors['danger'],
            background_normal='',
            color=self.colors['white'],
            font_size=25,
            bold=True
        )
        delete_btn.bind ( on_press=lambda x, p=product: self.delete_product_permanent ( p ) )
        buttons.add_widget ( delete_btn )

        card.add_widget ( buttons )
        self.product_grid.add_widget ( card )

    def show_add_product_dialog(self, instance):
        """Товар кошуу диалогу - профессионалдуу дизайн"""
        content = BoxLayout ( orientation='vertical', spacing=15, padding=20 )

        # Стилдүү аталыш
        title = Label (
            text="ЖАҢЫ ТОВАР КОШУУ",
            font_size=20,
            bold=True,
            color=self.colors['primary'],
            size_hint_y=0.08
        )
        content.add_widget ( title )

        # Форма талаалары
        name_input = TextInput (
            hint_text="Товардын аты",
            multiline=False,
            font_size=25,
            padding=[15, 12, 15, 12],
            size_hint_y=0.12
        )
        content.add_widget ( name_input )

        # Баа жана сан кошо турган контейнер
        price_stock = BoxLayout ( spacing=15, size_hint_y=0.12 )
        price_input = TextInput (
            hint_text="Баасы (сом)",
            multiline=False,
            input_filter='float',
            font_size=30,
            padding=[15, 12, 15, 12]
        )
        price_stock.add_widget ( price_input )

        stock_input = TextInput (
            hint_text="Баштапкы саны",
            multiline=False,
            input_filter='float',
            text="0",
            font_size=20,
            padding=[15, 12, 15, 12]
        )
        price_stock.add_widget ( stock_input )
        content.add_widget ( price_stock )

        # Категория жана бирдик
        cat_unit = BoxLayout ( spacing=15, size_hint_y=0.12 )
        categories = self.product_manager.get_all_categories ()
        category_spinner = Spinner (
            text="Категория тандаңыз",
            values=[c.name for c in categories],
            font_size=25,
            size_hint_x=0.5
        )
        cat_unit.add_widget ( category_spinner )

        unit_spinner = Spinner (
            text="Өлчөм бирдиги",
            values=[u.value for u in UnitType],
            font_size=25,
            size_hint_x=0.5
        )
        cat_unit.add_widget ( unit_spinner )
        content.add_widget ( cat_unit )

        barcode_input = TextInput (
            hint_text="Штрихкод (милдеттүү эмес)",
            multiline=False,
            font_size=20,
            padding=[15, 12, 15, 12],
            size_hint_y=0.1
        )
        content.add_widget ( barcode_input )

        # Кнопкалар
        btn_layout = BoxLayout ( spacing=15, size_hint_y=0.12 )
        save_btn = Button (
            text="💾 САКТОО",
            background_color=self.colors['success'],
            background_normal='',
            color=self.colors['white'],
            font_size=20,
            bold=True
        )
        cancel_btn = Button (
            text="❌ ЖОККО ЧЫГАРУУ",
            background_color=self.colors['danger'],
            background_normal='',
            color=self.colors['white'],
            font_size=20,
            bold=True
        )

        popup = Popup (
            title="",
            content=content,
            size_hint=(0.5, 0.6),
            background_color=self.colors['white'],
            separator_color=self.colors['primary']
        )

        def save_product(instance):
            if not name_input.text or not price_input.text:
                self.show_message ( "Ката", "Товардын аты жана баасы милдеттүү!" )
                return

            category = next ( (c for c in categories if c.name == category_spinner.text), None )
            if not category:
                self.show_message ( "Ката", "Категория тандаңыз!" )
                return

            unit = next ( (u for u in UnitType if u.value == unit_spinner.text), UnitType.PIECE )

            success, result = self.product_manager.add_product (
                name=name_input.text,
                price=float ( price_input.text ),
                category_id=category.id,
                unit_type=unit,
                stock=float ( stock_input.text ) if stock_input.text else 0,
                barcode=barcode_input.text if barcode_input.text else None
            )

            if success:
                popup.dismiss ()
                self.load_products ()
                self.show_message ( "Ийгиликтүү", "Товар ийгиликтүү кошулду!" )
            else:
                self.show_message ( "Ката", result )

        save_btn.bind ( on_press=save_product )
        cancel_btn.bind ( on_press=popup.dismiss )

        btn_layout.add_widget ( save_btn )
        btn_layout.add_widget ( cancel_btn )
        content.add_widget ( btn_layout )

        popup.open ()

    def show_edit_product_dialog(self, product):
        """Товарды түзөтүү диалогу"""
        content = BoxLayout ( orientation='vertical', spacing=15, padding=20 )

        title = Label (
            text="ТОВАРДЫ ТҮЗӨТҮҮ",
            font_size=25,
            bold=True,
            color=self.colors['primary'],
            size_hint_y=0.08
        )
        content.add_widget ( title )

        name_input = TextInput (
            text=product.name,
            multiline=False,
            font_size=35,
            padding=[15, 12, 15, 12],
            size_hint_y=0.12
        )
        content.add_widget ( name_input )

        price_input = TextInput (
            text=str ( product.price ),
            multiline=False,
            input_filter='float',
            font_size=30,
            padding=[15, 12, 15, 12],
            size_hint_y=0.12
        )
        content.add_widget ( price_input )

        categories = self.product_manager.get_all_categories ()
        category_names = [c.name for c in categories]
        current_category = product.category.name if product.category else ""
        category_spinner = Spinner (
            text=current_category,
            values=category_names,
            font_size=25,
            size_hint_y=0.12
        )
        content.add_widget ( category_spinner )

        unit_spinner = Spinner (
            text=product.unit_type.value,
            values=[u.value for u in UnitType],
            font_size=30,
            size_hint_y=0.12
        )
        content.add_widget ( unit_spinner )

        btn_layout = BoxLayout ( spacing=15, size_hint_y=0.12 )
        save_btn = Button (
            text="💾 САКТОО",
            background_color=self.colors['success'],
            background_normal='',
            color=self.colors['white'],
            font_size=30,
            bold=True
        )
        cancel_btn = Button (
            text="❌ ЖОККО ЧЫГАРУУ",
            background_color=self.colors['danger'],
            background_normal='',
            color=self.colors['white'],
            font_size=30,
            bold=True
        )

        popup = Popup (
            title="",
            content=content,
            size_hint=(0.7, 0.70),
            background_color=self.colors['white'],
            separator_color=self.colors['primary']
        )

        def save_changes(instance):
            category = next ( (c for c in categories if c.name == category_spinner.text), None )
            unit = next ( (u for u in UnitType if u.value == unit_spinner.text), product.unit_type )

            success, result = self.product_manager.update_product (
                product.id,
                name=name_input.text,
                price=float ( price_input.text ),
                category_id=category.id if category else None,
                unit_type=unit
            )

            if success:
                popup.dismiss ()
                self.load_products ()
                self.show_message ( "Ийгиликтүү", "Товар ийгиликтүү жаңыртылды!" )
            else:
                self.show_message ( "Ката", result )

        save_btn.bind ( on_press=save_changes )
        cancel_btn.bind ( on_press=popup.dismiss )

        btn_layout.add_widget ( save_btn )
        btn_layout.add_widget ( cancel_btn )
        content.add_widget ( btn_layout )

        popup.open ()

    def archive_product(self, product):
        """Товарды архивге жөнөтүү"""
        content = BoxLayout ( orientation='vertical', spacing=15, padding=20 )

        content.add_widget ( Label (
            text=f"'{product.name}' товарын архивге жөнөтүү?",
            font_size=16,
            color=self.colors['dark']
        ) )
        content.add_widget ( Label (
            text="Архивдеги товар сатууда көрүнбөйт",
            font_size=12,
            color=self.colors['gray']
        ) )

        btn_layout = BoxLayout ( spacing=15, size_hint_y=0.3 )
        yes_btn = Button (
            text="Ооба, архивге",
            background_color=self.colors['warning'],
            background_normal='',
            color=self.colors['white'],
            font_size=20,
            bold=True
        )
        no_btn = Button (
            text="Жок",
            background_color=self.colors['gray'],
            background_normal='',
            color=self.colors['white'],
            font_size=20
        )

        popup = Popup (
            title="Архивге жөнөтүү",
            content=content,
            size_hint=(0.7, 0.70),
            background_color=self.colors['white']
        )

        def confirm_archive(instance):
            success, result = self.product_manager.archive_product ( product.id )
            if success:
                popup.dismiss ()
                self.load_products ()
                self.show_message ( "Ийгиликтүү", f"'{product.name}' архивацияланды!" )
            else:
                self.show_message ( "Ката", result )

        yes_btn.bind ( on_press=confirm_archive )
        no_btn.bind ( on_press=popup.dismiss )

        btn_layout.add_widget ( yes_btn )
        btn_layout.add_widget ( no_btn )
        content.add_widget ( btn_layout )

        popup.open ()

    def restore_product(self, product):
        """Архивден калыбына келтирүү"""
        content = BoxLayout ( orientation='vertical', spacing=15, padding=20 )

        content.add_widget ( Label (
            text=f"'{product.name}' товарын калыбына келтирүү?",
            font_size=16,
            color=self.colors['dark']
        ) )
        content.add_widget ( Label (
            text="Товар кайра сатууда көрүнөт",
            font_size=12,
            color=self.colors['gray']
        ) )

        btn_layout = BoxLayout ( spacing=15, size_hint_y=0.3 )
        yes_btn = Button (
            text="Ооба, калыбына келтирүү",
            background_color=self.colors['success'],
            background_normal='',
            color=self.colors['white'],
            font_size=20,
            bold=True
        )
        no_btn = Button (
            text="Жок",
            background_color=self.colors['gray'],
            background_normal='',
            color=self.colors['white'],
            font_size=20
        )

        popup = Popup (
            title="Калыбына келтирүү",
            content=content,
            size_hint=(1, 0.7),
            background_color=self.colors['white']
        )

        def confirm_restore(instance):
            success, result = self.product_manager.restore_product ( product.id )
            if success:
                popup.dismiss ()
                self.load_products ()
                self.show_message ( "Ийгиликтүү", f"'{product.name}' калыбына келтирилди!" )
            else:
                self.show_message ( "Ката", result )

        yes_btn.bind ( on_press=confirm_restore )
        no_btn.bind ( on_press=popup.dismiss )

        btn_layout.add_widget ( yes_btn )
        btn_layout.add_widget ( no_btn )
        content.add_widget ( btn_layout )

        popup.open ()

    def delete_product_permanent(self, product):
        """Товарды толугу менен өчүрүү"""
        content = BoxLayout ( orientation='vertical', spacing=15, padding=20 )

        content.add_widget ( Label (
            text="⚠️ КАТУУ ЭСКЕРТҮҮ!",
            font_size=20,
            bold=True,
            color=self.colors['danger']
        ) )
        content.add_widget ( Label (
            text=f"'{product.name}' товарын ТОЛУК өчүрүү?",
            font_size=16,
            color=self.colors['dark']
        ) )
        content.add_widget ( Label (
            text="Бул товар менен байланышкан бардык сатуулар да өчүрүлөт!\nБул аракетти кайтаруу мүмкүн ЭМЕС!",
            font_size=20,
            color=self.colors['warning']
        ) )

        btn_layout = BoxLayout ( spacing=15, size_hint_y=0.25 )
        yes_btn = Button (
            text="Ооба, толук өчүрүү",
            background_color=self.colors['danger'],
            background_normal='',
            color=self.colors['white'],
            font_size=25,
            bold=True
        )
        no_btn = Button (
            text="Жок",
            background_color=self.colors['gray'],
            background_normal='',
            color=self.colors['white'],
            font_size=25
        )

        popup = Popup (
            title="Толук өчүрүү",
            content=content,
            size_hint=(0.4, 1),
            background_color=self.colors['white']
        )

        def confirm_delete(instance):
            success, result = self.product_manager.delete_product_permanent ( product.id )
            if success:
                popup.dismiss ()
                self.load_products ()
                self.show_message ( "Ийгиликтүү", result )
            else:
                self.show_message ( "Ката", result )

        yes_btn.bind ( on_press=confirm_delete )
        no_btn.bind ( on_press=popup.dismiss )

        btn_layout.add_widget ( yes_btn )
        btn_layout.add_widget ( no_btn )
        content.add_widget ( btn_layout )

        popup.open ()

    def update_stock(self, product):
        """Складды жаңыртуу"""
        content = BoxLayout ( orientation='vertical', spacing=15, padding=20 )

        current_stock = BoxLayout ( orientation='vertical', spacing=5, size_hint_y=0.3 )
        current_stock.add_widget ( Label (
            text=f"{product.name}",
            font_size=50,
            bold=True,
            color=self.colors['primary']
        ) )
        current_stock.add_widget ( Label (
            text=f"Учурдагы сан: {product.stock:,.0f} {product.unit_type.value}",
            font_size=40,
            color=self.colors['dark']
        ) )
        content.add_widget ( current_stock )

        stock_input = TextInput (
            hint_text="Санды киргизиңиз (минус менен азайтуу)",
            multiline=False,
            input_filter='float',
            font_size=20,
            padding=[15, 12, 15, 12],
            size_hint_y=0.15
        )
        content.add_widget ( stock_input )

        btn_layout = BoxLayout ( spacing=15, size_hint_y=0.12 )
        update_btn = Button (
            text="📦 ЖАҢЫРТУУ",
            background_color=self.colors['success'],
            background_normal='',
            color=self.colors['white'],
            font_size=16,
            bold=True
        )
        cancel_btn = Button (
            text="❌ ЖАБУУ",
            background_color=self.colors['danger'],
            background_normal='',
            color=self.colors['white'],
            font_size=16,
            bold=True
        )

        popup = Popup (
            title="Складды жаңыртуу",
            content=content,
            size_hint=(0.7, 0.70),
            background_color=self.colors['white']
        )

        def do_update(instance):
            try:
                quantity = float ( stock_input.text ) if stock_input.text else 0
                success, result = self.product_manager.update_stock ( product.id, quantity )
                if success:
                    popup.dismiss ()
                    self.load_products ()
                    self.show_message ( "Ийгиликтүү",
                                        f"Склад жаңыртылды!\nЖаңы сан: {result:,.0f} {product.unit_type.value}" )
                else:
                    self.show_message ( "Ката", result )
            except ValueError:
                self.show_message ( "Ката", "Туура сан киргизиңиз!" )

        update_btn.bind ( on_press=do_update )
        cancel_btn.bind ( on_press=popup.dismiss )

        btn_layout.add_widget ( update_btn )
        btn_layout.add_widget ( cancel_btn )
        content.add_widget ( btn_layout )

        popup.open ()

    def show_message(self, title, message):
        """Билдирүү көрсөтүү"""
        content = BoxLayout ( orientation='vertical', spacing=15, padding=20 )

        icon = "✅" if "Ийгиликтүү" in title else "❌"
        content.add_widget ( Label (
            text=f"{icon} {message}",
            font_size=18,
            color=self.colors['dark'],
            halign='center'
        ) )

        btn = Button (
            text="ТҮШҮНДҮМ",
            size_hint_y=0.3,
            background_color=self.colors['primary'],
            background_normal='',
            color=self.colors['white'],
            font_size=14,
            bold=True
        )

        popup = Popup (
            title=title,
            content=content,
            size_hint=(0.35, 0.25),
            background_color=self.colors['white']
        )

        btn.bind ( on_press=popup.dismiss )
        content.add_widget ( btn )

        popup.open ()