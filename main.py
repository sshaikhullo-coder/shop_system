"""
Дүкөн башкаруу системасы - Жөнөкөй жана ишенимдүү версия
"""

import sqlite3
from datetime import datetime
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.core.window import Window
from kivy.graphics import Color, RoundedRectangle

# Терезе өлчөмү
Window.size = (1000, 700)
Window.clearcolor = (0.95, 0.95, 0.95, 1)


# ============== МААЛЫМАТ БАЗАСЫ ==============
class Database:
    def __init__(self):
        self.conn = sqlite3.connect ( 'shop.db' )
        self.cursor = self.conn.cursor ()
        self.create_tables ()

    def create_tables(self):
        # Категориялар
        self.cursor.execute ( '''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
        ''' )

        # Товарлар
        self.cursor.execute ( '''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price REAL NOT NULL,
                stock REAL NOT NULL DEFAULT 0,
                unit TEXT DEFAULT 'даана',
                category_id INTEGER,
                is_active INTEGER DEFAULT 1
            )
        ''' )

        # Колдонуучулар
        self.cursor.execute ( '''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                full_name TEXT NOT NULL,
                role TEXT DEFAULT 'cashier'
            )
        ''' )

        # Баштапкы категориялар
        self.cursor.execute ( "INSERT OR IGNORE INTO categories (name) VALUES ('Жалпы')" )
        self.cursor.execute ( "INSERT OR IGNORE INTO categories (name) VALUES ('Азык-түлүк')" )
        self.cursor.execute ( "INSERT OR IGNORE INTO categories (name) VALUES ('Суусундуктар')" )

        # Башкы администратор
        self.cursor.execute ( "SELECT * FROM users WHERE username='admin'" )
        if not self.cursor.fetchone ():
            self.cursor.execute ( "INSERT INTO users (username, password, full_name, role) VALUES (?, ?, ?, ?)",
                                  ('admin', 'admin123', 'Администратор', 'admin') )

        # Демо товарлар
        self.cursor.execute ( "SELECT * FROM products LIMIT 1" )
        if not self.cursor.fetchone ():
            demo_products = [
                ('Алма', 50, 100, 'кг'),
                ('Нан', 30, 50, 'даана'),
                ('Сүт', 80, 30, 'литр'),
                ('Кант', 65, 40, 'кг'),
                ('Чай', 120, 25, 'пачка'),
            ]
            self.cursor.executemany ( "INSERT INTO products (name, price, stock, unit) VALUES (?, ?, ?, ?)",
                                      demo_products )

        self.conn.commit ()
        print ( "✅ Маалымат базасы даяр!" )

    def execute(self, query, params=()):
        self.cursor.execute ( query, params )
        self.conn.commit ()
        return self.cursor


db = Database ()


# ============== КИРҮҮ ЭКРАНЫ ==============
class LoginScreen ( Screen ):
    def __init__(self, **kwargs):
        super ().__init__ ( **kwargs )
        layout = BoxLayout ( orientation='vertical', padding=50, spacing=20 )

        # Аталыш
        layout.add_widget ( Label ( text='🏪 ДҮКӨН БАШКАРУУ СИСТЕМАСЫ', font_size=32, bold=True ) )
        layout.add_widget ( Label ( text='Кирүү', font_size=24, size_hint_y=0.1 ) )

        # Форма
        self.username = TextInput ( hint_text='Колдонуучу аты', size_hint_y=0.1, font_size=18 )
        self.password = TextInput ( hint_text='Пароль', password=True, size_hint_y=0.1, font_size=18 )
        layout.add_widget ( self.username )
        layout.add_widget ( self.password )

        # Кирүү кнопкасы
        btn = Button ( text='КИРҮҮ', size_hint_y=0.1, background_color=(0.2, 0.6, 0.8, 1), font_size=20 )
        btn.bind ( on_press=self.login )
        layout.add_widget ( btn )

        # Маалымат
        layout.add_widget ( Label ( text='Демо: admin / admin123', size_hint_y=0.1, font_size=12 ) )

        self.add_widget ( layout )

    def login(self, instance):
        username = self.username.text.strip ()
        password = self.password.text

        db.cursor.execute ( "SELECT * FROM users WHERE username=? AND password=?", (username, password) )
        user = db.cursor.fetchone ()

        if user:
            self.manager.current = 'dashboard'
            self.manager.get_screen ( 'dashboard' ).set_user ( user )
        else:
            popup = Popup ( title='Ката', content=Label ( text='Колдонуучу же пароль туура эмес!' ),
                            size_hint=(0.5, 0.3) )
            popup.open ()


# ============== БАШКЫ ПАНЕЛЬ ==============
class DashboardScreen ( Screen ):
    def __init__(self, **kwargs):
        super ().__init__ ( **kwargs )
        self.user = None
        layout = BoxLayout ( orientation='vertical', padding=10, spacing=10 )

        # Башкы панель
        header = BoxLayout ( size_hint_y=0.1, spacing=10 )
        header.add_widget ( Label ( text='🏠 БАШКЫ ПАНЕЛЬ', font_size=24, bold=True ) )
        self.user_label = Label ( text='', font_size=16 )
        header.add_widget ( self.user_label )

        logout_btn = Button ( text='Чыгуу', size_hint_x=0.15, background_color=(0.8, 0.2, 0.2, 1) )
        logout_btn.bind ( on_press=self.logout )
        header.add_widget ( logout_btn )
        layout.add_widget ( header )

        # Статистика
        stats = BoxLayout ( size_hint_y=0.15, spacing=10, padding=10 )

        # Товарлардын саны
        db.cursor.execute ( "SELECT COUNT(*) FROM products WHERE is_active=1" )
        product_count = db.cursor.fetchone ()[0]
        stats.add_widget ( self.create_stat_card ( "📦 Товарлар", str ( product_count ), (0.2, 0.6, 0.8, 1) ) )

        # Жалпы баа
        db.cursor.execute ( "SELECT SUM(price * stock) FROM products WHERE is_active=1" )
        total_value = db.cursor.fetchone ()[0] or 0
        stats.add_widget ( self.create_stat_card ( "💰 Склад баасы", f"{total_value:,.0f} сом", (0.2, 0.7, 0.3, 1) ) )

        layout.add_widget ( stats )

        # Кнопкалар
        buttons = GridLayout ( cols=2, spacing=20, size_hint_y=0.5, padding=50 )

        btn1 = Button ( text='📦 ТОВАРЛАР', background_color=(0.2, 0.6, 0.8, 1), font_size=24 )
        btn1.bind ( on_press=lambda x: setattr ( self.manager, 'current', 'products' ) )

        btn2 = Button ( text='🛒 САТУУ', background_color=(0.2, 0.7, 0.3, 1), font_size=24 )
        btn2.bind ( on_press=lambda x: setattr ( self.manager, 'current', 'sale' ) )

        btn3 = Button ( text='📊 ОТЧЕТТОР', background_color=(0.9, 0.6, 0.1, 1), font_size=24 )
        btn3.bind ( on_press=lambda x: setattr ( self.manager, 'current', 'reports' ) )

        btn4 = Button ( text='👥 КОЛДОНУУЧУЛАР', background_color=(0.4, 0.4, 0.4, 1), font_size=24 )
        btn4.bind ( on_press=lambda x: setattr ( self.manager, 'current', 'users' ) )

        buttons.add_widget ( btn1 )
        buttons.add_widget ( btn2 )
        buttons.add_widget ( btn3 )
        buttons.add_widget ( btn4 )
        layout.add_widget ( buttons )

        self.add_widget ( layout )

    def create_stat_card(self, title, value, color):
        card = BoxLayout ( orientation='vertical', padding=10, spacing=5 )
        with card.canvas.before:
            Color ( 1, 1, 1, 1 )
            RoundedRectangle ( size=card.size, pos=card.pos, radius=[10] )
        card.add_widget ( Label ( text=title, font_size=16, bold=True ) )
        card.add_widget ( Label ( text=value, font_size=24, bold=True, color=color ) )
        return card

    def set_user(self, user):
        self.user = user
        self.user_label.text = f'👤 {user[3]} ({user[4]})'

    def logout(self, instance):
        self.manager.current = 'login'


# ============== ТОВАРЛАР ЭКРАНЫ ==============
class ProductsScreen ( Screen ):
    def __init__(self, **kwargs):
        super ().__init__ ( **kwargs )
        layout = BoxLayout ( orientation='vertical', padding=10, spacing=10 )

        # Башкы панель
        header = BoxLayout ( size_hint_y=0.08, spacing=10 )
        back_btn = Button ( text='←', size_hint_x=0.1, font_size=24 )
        back_btn.bind ( on_press=lambda x: setattr ( self.manager, 'current', 'dashboard' ) )
        header.add_widget ( back_btn )
        header.add_widget ( Label ( text='📦 ТОВАРЛАР', font_size=24, bold=True ) )

        # Издөө
        self.search_input = TextInput ( hint_text='🔍 Издөө...', size_hint_x=0.5, font_size=16 )
        header.add_widget ( self.search_input )

        search_btn = Button ( text='Издөө', size_hint_x=0.15 )
        search_btn.bind ( on_press=self.search_products )
        header.add_widget ( search_btn )

        refresh_btn = Button ( text='🔄', size_hint_x=0.1 )
        refresh_btn.bind ( on_press=lambda x: self.load_products () )
        header.add_widget ( refresh_btn )

        layout.add_widget ( header )

        # Товарлар тизмеси
        self.scroll = ScrollView ()
        self.products_grid = GridLayout ( cols=1, size_hint_y=None, spacing=10, padding=10 )
        self.products_grid.bind ( minimum_height=self.products_grid.setter ( 'height' ) )
        self.scroll.add_widget ( self.products_grid )
        layout.add_widget ( self.scroll )

        # Кошуу кнопкасы
        add_btn = Button ( text='➕ ЖАҢЫ ТОВАР КОШУУ', size_hint_y=0.08, background_color=(0.2, 0.7, 0.3, 1),
                           font_size=18 )
        add_btn.bind ( on_press=self.show_add_dialog )
        layout.add_widget ( add_btn )

        self.add_widget ( layout )
        self.load_products ()

    def load_products(self, search=''):
        self.products_grid.clear_widgets ()

        if search:
            db.cursor.execute ( "SELECT * FROM products WHERE name LIKE ? AND is_active=1", (f'%{search}%',) )
        else:
            db.cursor.execute ( "SELECT * FROM products WHERE is_active=1 ORDER BY name" )

        products = db.cursor.fetchall ()

        if not products:
            self.products_grid.add_widget ( Label ( text='📭 Товар жок', size_hint_y=None, height=100, font_size=18 ) )
        else:
            for p in products:
                self.add_product_card ( p )

    def add_product_card(self, product):
        card = BoxLayout ( size_hint_y=None, height=80, spacing=10, padding=10 )

        with card.canvas.before:
            Color ( 1, 1, 1, 1 )
            RoundedRectangle ( size=card.size, pos=card.pos, radius=[10] )

        info = BoxLayout ( orientation='vertical', size_hint_x=0.6 )
        info.add_widget ( Label ( text=product[1], font_size=16, bold=True, halign='left' ) )
        info.add_widget ( Label ( text=f"💰 {product[2]:,.0f} сом  |  📦 {product[3]:.0f} {product[4]}",
                                  font_size=14, halign='left' ) )
        card.add_widget ( info )

        buttons = BoxLayout ( size_hint_x=0.4, spacing=5 )

        edit_btn = Button ( text='✏️', background_color=(0.2, 0.5, 0.8, 1) )
        edit_btn.bind ( on_press=lambda x, p=product: self.show_edit_dialog ( p ) )

        stock_btn = Button ( text='📦', background_color=(0.2, 0.7, 0.3, 1) )
        stock_btn.bind ( on_press=lambda x, p=product: self.update_stock ( p ) )

        delete_btn = Button ( text='🗑️', background_color=(0.8, 0.2, 0.2, 1) )
        delete_btn.bind ( on_press=lambda x, p=product: self.delete_product ( p ) )

        buttons.add_widget ( edit_btn )
        buttons.add_widget ( stock_btn )
        buttons.add_widget ( delete_btn )
        card.add_widget ( buttons )

        self.products_grid.add_widget ( card )

    def search_products(self, instance):
        self.load_products ( self.search_input.text )

    def show_add_dialog(self, instance):
        content = BoxLayout ( orientation='vertical', spacing=10, padding=20 )

        name = TextInput ( hint_text='Товардын аты', font_size=16 )
        price = TextInput ( hint_text='Баасы', input_filter='float', font_size=16 )
        stock = TextInput ( hint_text='Саны', text='0', input_filter='float', font_size=16 )

        content.add_widget ( name )
        content.add_widget ( price )
        content.add_widget ( stock )

        btn_layout = BoxLayout ( spacing=10, size_hint_y=0.3 )
        save_btn = Button ( text='САКТОО', background_color=(0.2, 0.7, 0.3, 1) )
        cancel_btn = Button ( text='ЖОК', background_color=(0.8, 0.2, 0.2, 1) )

        popup = Popup ( title='Жаңы товар', content=content, size_hint=(0.5, 0.5) )

        def save(instance):
            if name.text and price.text:
                db.execute ( "INSERT INTO products (name, price, stock) VALUES (?, ?, ?)",
                             (name.text, float ( price.text ), float ( stock.text )) )
                popup.dismiss ()
                self.load_products ()

        save_btn.bind ( on_press=save )
        cancel_btn.bind ( on_press=popup.dismiss )
        btn_layout.add_widget ( save_btn )
        btn_layout.add_widget ( cancel_btn )
        content.add_widget ( btn_layout )

        popup.open ()

    def show_edit_dialog(self, product):
        content = BoxLayout ( orientation='vertical', spacing=10, padding=20 )

        name = TextInput ( text=product[1], font_size=16 )
        price = TextInput ( text=str ( product[2] ), input_filter='float', font_size=16 )

        content.add_widget ( name )
        content.add_widget ( price )

        btn_layout = BoxLayout ( spacing=10, size_hint_y=0.3 )
        save_btn = Button ( text='САКТОО', background_color=(0.2, 0.7, 0.3, 1) )
        cancel_btn = Button ( text='ЖОК', background_color=(0.8, 0.2, 0.2, 1) )

        popup = Popup ( title='Түзөтүү', content=content, size_hint=(0.5, 0.4) )

        def save(instance):
            db.execute ( "UPDATE products SET name=?, price=? WHERE id=?",
                         (name.text, float ( price.text ), product[0]) )
            popup.dismiss ()
            self.load_products ()

        save_btn.bind ( on_press=save )
        cancel_btn.bind ( on_press=popup.dismiss )
        btn_layout.add_widget ( save_btn )
        btn_layout.add_widget ( cancel_btn )
        content.add_widget ( btn_layout )

        popup.open ()

    def update_stock(self, product):
        content = BoxLayout ( orientation='vertical', spacing=10, padding=20 )

        content.add_widget ( Label ( text=f"{product[1]}", font_size=18, bold=True ) )
        content.add_widget ( Label ( text=f"Учурдагы: {product[3]} {product[4]}", font_size=16 ) )

        stock = TextInput ( hint_text='Санды киргизиңиз (+/-)', font_size=16 )
        content.add_widget ( stock )

        btn_layout = BoxLayout ( spacing=10, size_hint_y=0.3 )
        update_btn = Button ( text='ЖАҢЫРТУУ', background_color=(0.2, 0.7, 0.3, 1) )
        cancel_btn = Button ( text='ЖОК', background_color=(0.8, 0.2, 0.2, 1) )

        popup = Popup ( title='Складды жаңыртуу', content=content, size_hint=(0.5, 0.45) )

        def update(instance):
            try:
                qty = float ( stock.text )
                new_stock = product[3] + qty
                if new_stock >= 0:
                    db.execute ( "UPDATE products SET stock=? WHERE id=?", (new_stock, product[0]) )
                    popup.dismiss ()
                    self.load_products ()
                else:
                    error = Popup ( title='Ката', content=Label ( text='Сан терс болушу мүмкүн эмес!' ),
                                    size_hint=(0.5, 0.3) )
                    error.open ()
            except:
                error = Popup ( title='Ката', content=Label ( text='Туура сан киргизиңиз!' ), size_hint=(0.5, 0.3) )
                error.open ()

        update_btn.bind ( on_press=update )
        cancel_btn.bind ( on_press=popup.dismiss )
        btn_layout.add_widget ( update_btn )
        btn_layout.add_widget ( cancel_btn )
        content.add_widget ( btn_layout )

        popup.open ()

    def delete_product(self, product):
        content = BoxLayout ( orientation='vertical', spacing=10, padding=20 )
        content.add_widget ( Label ( text=f"'{product[1]}' товарын өчүрүү?", font_size=16 ) )

        btn_layout = BoxLayout ( spacing=10, size_hint_y=0.3 )
        yes_btn = Button ( text='Ооба', background_color=(0.8, 0.2, 0.2, 1) )
        no_btn = Button ( text='Жок', background_color=(0.4, 0.4, 0.4, 1) )

        popup = Popup ( title='Өчүрүү', content=content, size_hint=(0.4, 0.3) )

        def delete(instance):
            db.execute ( "DELETE FROM products WHERE id=?", (product[0],) )
            popup.dismiss ()
            self.load_products ()

        yes_btn.bind ( on_press=delete )
        no_btn.bind ( on_press=popup.dismiss )
        btn_layout.add_widget ( yes_btn )
        btn_layout.add_widget ( no_btn )
        content.add_widget ( btn_layout )

        popup.open ()


# ============== БАШКА ЭКРАНДАР (ЖӨНӨКӨЙ) ==============
class SaleScreen ( Screen ):
    def __init__(self, **kwargs):
        super ().__init__ ( **kwargs )
        layout = BoxLayout ( orientation='vertical', padding=10, spacing=10 )

        header = BoxLayout ( size_hint_y=0.08, spacing=10 )
        back_btn = Button ( text='←', size_hint_x=0.1, font_size=24 )
        back_btn.bind ( on_press=lambda x: setattr ( self.manager, 'current', 'dashboard' ) )
        header.add_widget ( back_btn )
        header.add_widget ( Label ( text='🛒 САТУУ', font_size=24, bold=True ) )
        layout.add_widget ( header )

        content = Label ( text='🛒 Сатуу бөлүмү иштелип жатат...\n\nКечиресиз, бул бөлүм даярдалууда.',
                          font_size=18, color=(0.4, 0.4, 0.4, 1) )
        layout.add_widget ( content )
        self.add_widget ( layout )


class ReportsScreen ( Screen ):
    def __init__(self, **kwargs):
        super ().__init__ ( **kwargs )
        layout = BoxLayout ( orientation='vertical', padding=10, spacing=10 )

        header = BoxLayout ( size_hint_y=0.08, spacing=10 )
        back_btn = Button ( text='←', size_hint_x=0.1, font_size=24 )
        back_btn.bind ( on_press=lambda x: setattr ( self.manager, 'current', 'dashboard' ) )
        header.add_widget ( back_btn )
        header.add_widget ( Label ( text='📊 ОТЧЕТТОР', font_size=24, bold=True ) )
        layout.add_widget ( header )

        content = Label ( text='📊 Отчеттор бөлүмү иштелип жатат...\n\nКечиресиз, бул бөлүм даярдалууда.',
                          font_size=18, color=(0.4, 0.4, 0.4, 1) )
        layout.add_widget ( content )
        self.add_widget ( layout )


class UsersScreen ( Screen ):
    def __init__(self, **kwargs):
        super ().__init__ ( **kwargs )
        layout = BoxLayout ( orientation='vertical', padding=10, spacing=10 )

        header = BoxLayout ( size_hint_y=0.08, spacing=10 )
        back_btn = Button ( text='←', size_hint_x=0.1, font_size=24 )
        back_btn.bind ( on_press=lambda x: setattr ( self.manager, 'current', 'dashboard' ) )
        header.add_widget ( back_btn )
        header.add_widget ( Label ( text='👥 КОЛДОНУУЧУЛАР', font_size=24, bold=True ) )
        layout.add_widget ( header )

        # Колдонуучулардын тизмеси
        db.cursor.execute ( "SELECT id, username, full_name, role FROM users" )
        users = db.cursor.fetchall ()

        if users:
            for u in users:
                user_box = BoxLayout ( size_hint_y=None, height=50, spacing=10, padding=10 )
                with user_box.canvas.before:
                    Color ( 1, 1, 1, 1 )
                    RoundedRectangle ( size=user_box.size, pos=user_box.pos, radius=[5] )
                user_box.add_widget ( Label ( text=f"{u[1]}", font_size=16, bold=True ) )
                user_box.add_widget ( Label ( text=f"{u[2]}", font_size=14 ) )
                user_box.add_widget ( Label ( text=f"Роль: {u[3]}", font_size=14, color=(0.4, 0.4, 0.4, 1) ) )
                layout.add_widget ( user_box )
        else:
            layout.add_widget ( Label ( text='Колдонуучулар жок', font_size=18 ) )

        self.add_widget ( layout )


# ============== НЕГИЗГИ КОЛДОНМО ==============
class ShopSystemApp ( App ):
    def build(self):
        self.title = "Дүкөн Башкаруу Системасы"

        sm = ScreenManager ()
        sm.add_widget ( LoginScreen ( name='login' ) )
        sm.add_widget ( DashboardScreen ( name='dashboard' ) )
        sm.add_widget ( ProductsScreen ( name='products' ) )
        sm.add_widget ( SaleScreen ( name='sale' ) )
        sm.add_widget ( ReportsScreen ( name='reports' ) )
        sm.add_widget ( UsersScreen ( name='users' ) )

        return sm


if __name__ == '__main__':
    ShopSystemApp ().run ()