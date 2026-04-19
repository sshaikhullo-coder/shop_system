from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner
from kivy.graphics import Color, RoundedRectangle
from database.models import UserRole
from datetime import datetime


class UsersScreen ( BoxLayout ):
    def __init__(self, user_data, auth_manager, on_back, **kwargs):
        super ().__init__ ( **kwargs )
        self.orientation = 'vertical'
        self.user_data = user_data
        self.auth_manager = auth_manager
        self.on_back = on_back

        if not self.auth_manager.is_admin ():
            self.add_widget (
                Label ( text="⚠️ Уруксат жок! Бул бөлүм администратор үчүн.", color=(1, 0, 0, 1), font_size=16 ) )
            return

        self.init_ui ()
        self.load_users ()

    def init_ui(self):
        self.create_header ()
        self.create_user_list ()
        self.create_add_button ()

    def create_header(self):
        header = BoxLayout ( size_hint_y=0.08, padding=10, spacing=10 )
        with header.canvas.before:
            Color ( 0.2, 0.4, 0.6, 1 )
            RoundedRectangle ( size=header.size, pos=header.pos, radius=[10] )

        back_btn = Button ( text="← АРТКА", size_hint_x=0.12, background_color=(0.5, 0.5, 0.5, 1), bold=True )
        back_btn.bind ( on_press=lambda x: self.on_back () )
        header.add_widget ( back_btn )

        header.add_widget ( Label ( text="👥 КОЛДОНУУЧУЛАРДЫ БАШКАРУУ", color=(1, 1, 1, 1), font_size=18, bold=True ) )

        self.add_widget ( header )

    def create_user_list(self):
        self.user_layout = BoxLayout ( orientation='vertical', spacing=5, padding=10 )
        self.scroll = ScrollView ()
        self.user_grid = GridLayout ( cols=1, size_hint_y=None, spacing=5 )
        self.user_grid.bind ( minimum_height=self.user_grid.setter ( 'height' ) )
        self.scroll.add_widget ( self.user_grid )
        self.user_layout.add_widget ( self.scroll )
        self.add_widget ( self.user_layout )

    def create_add_button(self):
        add_btn = Button (
            text="➕ ЖАҢЫ КОЛДОНУУЧУ КОШУУ",
            size_hint_y=0.08,
            background_color=(0.2, 0.8, 0.2, 1),
            font_size=14,
            bold=True
        )
        add_btn.bind ( on_press=self.show_add_user_dialog )
        self.add_widget ( add_btn )

    def load_users(self):
        users = self.auth_manager.get_all_users ()
        self.user_grid.clear_widgets ()
        for user in users:
            self.add_user_card ( user )

    def add_user_card(self, user):
        card = BoxLayout ( size_hint_y=None, height=85, spacing=10, padding=10 )
        with card.canvas.before:
            Color ( 0.95, 0.95, 0.95, 1 )
            RoundedRectangle ( size=card.size, pos=card.pos, radius=[10] )

        info = BoxLayout ( orientation='vertical', size_hint_x=0.65 )
        info.add_widget ( Label ( text=user['full_name'], font_size=14, bold=True, halign='left' ) )
        info.add_widget ( Label ( text=f"👤 {user['username']}", font_size=11, halign='left' ) )

        role_text = "👑 АДМИН" if user['role'] == UserRole.ADMIN else "💼 МЕНЕДЖЕР" if user[
                                                                                         'role'] == UserRole.MANAGER else "🛒 КАССИР"
        status_text = "✅ АКТИВДҮҮ" if user['is_active'] else "❌ БЛОКТОЛГОН"
        info.add_widget ( Label ( text=f"{role_text} | {status_text}", font_size=10, color=(0.5, 0.5, 0.5, 1) ) )

        if user.get ( 'last_login' ):
            last_login = user['last_login']
            if isinstance ( last_login, datetime ):
                info.add_widget ( Label ( text=f"Соңку кирүү: {last_login.strftime ( '%d.%m.%Y' )}", font_size=9,
                                          color=(0.5, 0.5, 0.5, 1) ) )

        buttons = BoxLayout ( size_hint_x=0.35, spacing=5 )

        if user['id'] != self.user_data['id']:
            edit_btn = Button ( text="✏️ ӨЗГӨРТҮҮ", background_color=(0.3, 0.6, 0.9, 1), font_size=11 )
            edit_btn.bind ( on_press=lambda x, u=user: self.show_edit_user_dialog ( u ) )
            buttons.add_widget ( edit_btn )

            delete_btn = Button ( text="🗑 ӨЧҮРҮҮ", background_color=(0.8, 0.2, 0.2, 1), font_size=11 )
            delete_btn.bind ( on_press=lambda x, u=user: self.delete_user ( u ) )
            buttons.add_widget ( delete_btn )

        card.add_widget ( info )
        card.add_widget ( buttons )
        self.user_grid.add_widget ( card )

    def show_add_user_dialog(self, instance):
        content = BoxLayout ( orientation='vertical', spacing=10, padding=10 )

        fullname_input = TextInput ( hint_text="Толук аты-жөнү", multiline=False, font_size=12 )
        username_input = TextInput ( hint_text="Колдонуучу аты", multiline=False, font_size=12 )
        password_input = TextInput ( hint_text="Сырсөз", password=True, multiline=False, font_size=12 )

        role_spinner = Spinner ( text="КАССИР", values=["АДМИН", "МЕНЕДЖЕР", "КАССИР"], font_size=12 )
        role_map = {"АДМИН": UserRole.ADMIN, "МЕНЕДЖЕР": UserRole.MANAGER, "КАССИР": UserRole.CASHIER}

        btn_layout = BoxLayout ( spacing=10, size_hint_y=0.3 )
        save_btn = Button ( text="САКТОО", background_color=(0.2, 0.8, 0.2, 1), bold=True )
        cancel_btn = Button ( text="ЖОККО ЧЫГАРУУ", background_color=(0.8, 0.2, 0.2, 1), bold=True )

        popup = Popup ( title="Жаңы колдонуучу кошуу", content=content, size_hint=(0.7, 0.6) )

        def save_user(instance):
            if not username_input.text or not password_input.text:
                self.show_message ( "Ката", "Толук толтуруңуз" )
                return

            role = role_map[role_spinner.text]
            success, result = self.auth_manager.add_user (
                username=username_input.text,
                password=password_input.text,
                full_name=fullname_input.text or username_input.text,
                role=role.value
            )

            if success:
                popup.dismiss ()
                self.load_users ()
                self.show_message ( "Ийгиликтүү", "Колдонуучу кошулду" )
            else:
                self.show_message ( "Ката", result )

        save_btn.bind ( on_press=save_user )
        cancel_btn.bind ( on_press=popup.dismiss )

        content.add_widget ( fullname_input )
        content.add_widget ( username_input )
        content.add_widget ( password_input )
        content.add_widget ( role_spinner )
        content.add_widget ( btn_layout )
        btn_layout.add_widget ( save_btn )
        btn_layout.add_widget ( cancel_btn )

        popup.open ()

    def show_edit_user_dialog(self, user):
        content = BoxLayout ( orientation='vertical', spacing=10, padding=10 )

        fullname_input = TextInput ( text=user['full_name'] or "", multiline=False, font_size=12 )
        username_input = TextInput ( text=user['username'], multiline=False, font_size=12 )
        password_input = TextInput ( hint_text="Жаңы сырсөз (калтырса болот)", password=True, multiline=False,
                                     font_size=12 )

        role_options = ["АДМИН", "МЕНЕДЖЕР", "КАССИР"]
        current_role = "АДМИН" if user['role'] == UserRole.ADMIN else "МЕНЕДЖЕР" if user[
                                                                                        'role'] == UserRole.MANAGER else "КАССИР"
        role_spinner = Spinner ( text=current_role, values=role_options, font_size=12 )
        role_map = {"АДМИН": UserRole.ADMIN, "МЕНЕДЖЕР": UserRole.MANAGER, "КАССИР": UserRole.CASHIER}

        btn_layout = BoxLayout ( spacing=10, size_hint_y=0.3 )
        save_btn = Button ( text="САКТОО", background_color=(0.2, 0.8, 0.2, 1), bold=True )
        cancel_btn = Button ( text="ЖОККО ЧЫГАРУУ", background_color=(0.8, 0.2, 0.2, 1), bold=True )

        popup = Popup ( title="Колдонуучуну өзгөртүү", content=content, size_hint=(0.7, 0.6) )

        def save_user(instance):
            update_data = {
                'full_name': fullname_input.text,
                'username': username_input.text,
                'role': role_map[role_spinner.text]
            }
            if password_input.text:
                update_data['password'] = password_input.text

            success, result = self.auth_manager.update_user ( user['id'], **update_data )

            if success:
                popup.dismiss ()
                self.load_users ()
                self.show_message ( "Ийгиликтүү", "Колдонуучу өзгөртүлдү" )
            else:
                self.show_message ( "Ката", result )

        save_btn.bind ( on_press=save_user )
        cancel_btn.bind ( on_press=popup.dismiss )

        content.add_widget ( Label ( text=f"ID: {user['id']}", font_size=10 ) )
        content.add_widget ( fullname_input )
        content.add_widget ( username_input )
        content.add_widget ( password_input )
        content.add_widget ( role_spinner )
        content.add_widget ( btn_layout )
        btn_layout.add_widget ( save_btn )
        btn_layout.add_widget ( cancel_btn )

        popup.open ()

    def delete_user(self, user):
        content = BoxLayout ( orientation='vertical', spacing=10, padding=10 )
        content.add_widget ( Label ( text=f"'{user['full_name']}' колдонуучусун өчүрүү керекпи?", font_size=12 ) )

        btn_layout = BoxLayout ( spacing=10, size_hint_y=0.3 )
        yes_btn = Button ( text="ООБА", background_color=(0.8, 0.2, 0.2, 1), bold=True )
        no_btn = Button ( text="ЖОК", background_color=(0.5, 0.5, 0.5, 1), bold=True )

        popup = Popup ( title="Ырастоо", content=content, size_hint=(0.5, 0.3) )

        def confirm_delete(instance):
            success, result = self.auth_manager.delete_user ( user['id'] )
            if success:
                popup.dismiss ()
                self.load_users ()
                self.show_message ( "Ийгиликтүү", "Колдонуучу өчүрүлдү" )
            else:
                self.show_message ( "Ката", result )

        yes_btn.bind ( on_press=confirm_delete )
        no_btn.bind ( on_press=popup.dismiss )

        btn_layout.add_widget ( yes_btn )
        btn_layout.add_widget ( no_btn )
        content.add_widget ( btn_layout )

        popup.open ()

    def show_message(self, title, message):
        content = BoxLayout ( orientation='vertical', spacing=10, padding=10 )
        content.add_widget ( Label ( text=message, font_size=12 ) )
        btn = Button ( text="ЖАБУУ", size_hint_y=0.3, background_color=(0.3, 0.6, 0.9, 1) )
        popup = Popup ( title=title, content=content, size_hint=(0.5, 0.3) )
        btn.bind ( on_press=popup.dismiss )
        content.add_widget ( btn )
        popup.open ()