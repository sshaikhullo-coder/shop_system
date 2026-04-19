from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.checkbox import CheckBox
from kivy.clock import Clock


class LoginScreen ( BoxLayout ):
    def __init__(self, auth_manager, on_login_success, **kwargs):
        """
        auth_manager: AuthManager объектиси
        on_login_success: Логин ийгиликтүү болгондо чакырылуучу callback функция
        **kwargs: Kivy Widgetке берилүүчү башка параметрлер
        """
        # Белгисиз propertyлерди алып салуу
        # Эгер кандайдыр бир менеджерлер берилсе, аларды алып салабыз
        kwargs.pop ( 'db_manager', None )
        kwargs.pop ( 'user_manager', None )
        kwargs.pop ( 'product_manager', None )

        # Super конструкторду чакыруу
        super ().__init__ ( **kwargs )

        # Параметрлерди сактоо
        self.auth_manager = auth_manager
        self.on_login_success = on_login_success

        # UI түзүү
        self.orientation = 'vertical'
        self.padding = 50
        self.spacing = 20

        # Баш сөз
        self.title_label = Label (
            text='ДҮКӨН СИСТЕМАСЫНА КОШ КЕЛИҢИЗ!',
            font_size='24sp',
            size_hint=(1, 0.2),
            bold=True
        )
        self.add_widget ( self.title_label )

        # Роль тандоо
        role_layout = BoxLayout ( size_hint=(1, 0.1), spacing=10 )
        role_layout.add_widget ( Label ( text='Роль:', size_hint=(0.3, 1) ) )
        self.role_spinner = Spinner (
            text='Кассир',
            values=('Кассир', 'Администратор', 'Менеджер'),
            size_hint=(0.7, 1),
            background_color=(0.3, 0.5, 0.7, 1)
        )
        role_layout.add_widget ( self.role_spinner )
        self.add_widget ( role_layout )

        # Логин
        login_layout = BoxLayout ( size_hint=(1, 0.1), spacing=10 )
        login_layout.add_widget ( Label ( text='Логин:', size_hint=(0.3, 1) ) )
        self.login_input = TextInput (
            hint_text='Логиниңизди жазыңыз',
            size_hint=(0.7, 1),
            multiline=False
        )
        login_layout.add_widget ( self.login_input )
        self.add_widget ( login_layout )

        # Пароль
        password_layout = BoxLayout ( size_hint=(1, 0.1), spacing=10 )
        password_layout.add_widget ( Label ( text='Пароль:', size_hint=(0.3, 1) ) )
        self.password_input = TextInput (
            hint_text='Паролиңизди жазыңыз',
            size_hint=(0.7, 1),
            password=True,
            multiline=False
        )
        password_layout.add_widget ( self.password_input )
        self.add_widget ( password_layout )

        # Унутпа опциясы
        remember_layout = BoxLayout ( size_hint=(1, 0.1), spacing=10 )
        self.remember_check = CheckBox ( size_hint=(0.1, 1), active=False )
        remember_layout.add_widget ( self.remember_check )
        remember_layout.add_widget ( Label ( text='Мени унутпа', size_hint=(0.9, 1) ) )
        self.add_widget ( remember_layout )

        # Баскычтар
        buttons_layout = BoxLayout ( size_hint=(1, 0.2), spacing=15 )

        self.login_button = Button (
            text='КИРҮҮ',
            background_color=(0.2, 0.6, 0.3, 1),
            font_size='16sp',
            bold=True
        )
        self.login_button.bind ( on_press=self.handle_login )
        buttons_layout.add_widget ( self.login_button )

        self.clear_button = Button (
            text='ТАЗАЛОО',
            background_color=(0.6, 0.3, 0.2, 1),
            font_size='16sp'
        )
        self.clear_button.bind ( on_press=self.clear_fields )
        buttons_layout.add_widget ( self.clear_button )

        self.add_widget ( buttons_layout )

        # Ката билдирүүсү үчүн
        self.error_label = Label (
            text='',
            color=(1, 0, 0, 1),
            size_hint=(1, 0.1),
            font_size='14sp'
        )
        self.add_widget ( self.error_label )

    def handle_login(self, instance):
        """Логин баскычы басылганда"""
        username = self.login_input.text.strip ()
        password = self.password_input.text.strip ()
        role_text = self.role_spinner.text

        # Ролду англисчеге которуу
        role_map = {
            'Кассир': 'cashier',
            'Администратор': 'admin',
            'Менеджер': 'manager'
        }
        role = role_map.get ( role_text, 'cashier' )

        # Текшерүү
        if not username or not password:
            self.show_error ( 'Логин жана пароль толтурулушу керек!' )
            return

        # Аутентификация
        user = self.auth_manager.authenticate ( username, password, role )

        if user:
            # Ийгиликтүү логин
            self.show_error ( '', is_error=False )
            if self.remember_check.active:
                # Эгер "Мени унутпа" белгиленсе, маалыматты сактоо
                self.save_login_info ( username, role_text )

            # Callback функцияны чакыруу
            if self.on_login_success:
                self.on_login_success ( user )
        else:
            self.show_error ( 'Логин, пароль же роль туура эмес!' )

    def clear_fields(self, instance):
        """Тазалоо баскычы"""
        self.login_input.text = ''
        self.password_input.text = ''
        self.role_spinner.text = 'Кассир'
        self.remember_check.active = False
        self.show_error ( '' )

    def show_error(self, message, is_error=True):
        """Ката билдирүүсүн көрсөтүү"""
        self.error_label.text = message
        if is_error and message:
            self.error_label.color = (1, 0, 0, 1)
        else:
            self.error_label.color = (0, 1, 0, 1)

        # 3 секунддан кийин билдирүүнү тазалоо
        if message and is_error:
            Clock.schedule_once ( lambda dt: self.clear_error_message (), 3 )

    def clear_error_message(self):
        """Ката билдирүүсүн тазалоо"""
        if self.error_label.text and self.error_label.color == (1, 0, 0, 1):
            self.error_label.text = ''

    def save_login_info(self, username, role):
        """Логин маалыматын сактоо"""
        # Бул жерде файлга же settingsке сактоого болот
        print ( f"Логин маалыматтары сакталды: {username}, {role}" )

    def on_touch_down(self, touch):
        """Экранды басканда клавиатураны жашыруу"""
        self.login_input.focus = False
        self.password_input.focus = False
        return super ().on_touch_down ( touch )