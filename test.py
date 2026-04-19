# main.py
import os
import sys
import logging
from datetime import datetime
from pathlib import Path

from kivy.config import Config
from kivy.core.window import Window
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.clock import Clock
from kivy.utils import platform

# Конфигурацияны эрте орнотуу
Config.set ( 'graphics', 'resizable', True )
Config.set ( 'graphics', 'width', '1280' )
Config.set ( 'graphics', 'height', '800' )
Config.set ( 'graphics', 'minimum_width', '1024' )
Config.set ( 'graphics', 'minimum_height', '600' )
Config.set ( 'kivy', 'exit_on_escape', False )

# Терезенин өлчөмүн орнотуу
Window.size = (1280, 800)
# Минималдуу өлчөмдү орнотуу - бул жерде эскертүү кетпейт
Window.minimum_width = 1024
Window.minimum_height = 600
Window.title = "Магазин Автоматташтыруу Тутуму v1.0"

# Папкаларды түзүү
for folder in ['logs', 'reports', 'receipts', 'backups', 'data']:
    Path ( folder ).mkdir ( exist_ok=True )

# Логгер
logging.basicConfig (
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler ( 'logs/shop_system.log', encoding='utf-8' ),
        logging.StreamHandler ()
    ]
)
logger = logging.getLogger ( __name__ )


class ShopSystemApp ( App ):
    title = "Магазин Автоматташтыруу Тутуму"

    def __init__(self, **kwargs):
        super ().__init__ ( **kwargs )
        self.db = None
        self.auth_manager = None
        self.product_manager = None
        self.sales_manager = None
        self.report_manager = None
        self.analytics_manager = None
        self.backup_manager = None
        self.current_user_data = None
        self.sm = None
        logger.info ( "Shop System иштеп баштады" )

    def build(self):
        try:
            # Базаны баштоо
            from database.db_manager import DatabaseManager
            self.db = DatabaseManager ()
            logger.info ( "База туташтырылды" )

            # Менеджерлерди баштоо
            from modules.auth import AuthManager
            from modules.products import ProductManager
            from modules.sales import SalesManager
            from modules.reports import ReportManager
            from modules.analytics import AnalyticsManager
            from modules.backup import BackupManager

            self.auth_manager = AuthManager ()
            self.product_manager = ProductManager ()
            self.sales_manager = SalesManager ()
            self.report_manager = ReportManager ()
            self.analytics_manager = AnalyticsManager ()
            self.backup_manager = BackupManager ()
            logger.info ( "Менеджерлер инициализацияланды" )

            # Screen Manager
            self.sm = ScreenManager ( transition=FadeTransition () )

            # Login экраны
            try:
                from gui.screens.login_screen import LoginScreen

                login_screen = Screen ( name='login' )
                login_widget = LoginScreen (
                    auth_manager=self.auth_manager,
                    on_login_success=self.on_login_success,
                    db_manager=self.db
                )
                login_screen.add_widget ( login_widget )
                self.sm.add_widget ( login_screen )
                self.sm.current = 'login'
                logger.info ( "Login экраны түзүлдү" )
            except ImportError as e:
                logger.error ( f"LoginScreen импорттоодо ката: {e}" )
                # Жөнөкөй экран түзүү
                from kivy.uix.label import Label
                login_screen = Screen ( name='login' )
                login_screen.add_widget ( Label ( text="Login экраны жок!\nФайлдарды текшериңиз", font_size=20 ) )
                self.sm.add_widget ( login_screen )
                self.sm.current = 'login'

            return self.sm

        except Exception as e:
            logger.error ( f"Ишке кирүүдө ката: {e}" )
            import traceback
            traceback.print_exc ()
            # Ката болсо дагы бир нерсени көрсөтүү
            from kivy.uix.label import Label
            root = Label ( text=f"Ката кетти:\n{str ( e )}", font_size=20 )
            return root

    def on_login_success(self, user_data):
        self.current_user_data = user_data
        logger.info ( f"Кирди: {user_data['username']} ({user_data['role']})" )
        self.create_main_screens ()
        self.sm.current = 'dashboard'

    def create_main_screens(self):
        try:
            # Dashboard
            if not self.sm.has_screen ( 'dashboard' ):
                try:
                    from gui.screens.dashboard_screen import DashboardScreen

                    dashboard = Screen ( name='dashboard' )
                    dashboard_widget = DashboardScreen (
                        user_data=self.current_user_data,
                        product_manager=self.product_manager,
                        sales_manager=self.sales_manager,
                        analytics_manager=self.analytics_manager,
                        on_navigate=self.navigate_to
                    )
                    dashboard.add_widget ( dashboard_widget )
                    self.sm.add_widget ( dashboard )
                    logger.info ( "Dashboard экраны түзүлдү" )
                except ImportError as e:
                    logger.error ( f"DashboardScreen импорттоодо ката: {e}" )
                    from kivy.uix.label import Label
                    dashboard = Screen ( name='dashboard' )
                    dashboard.add_widget ( Label ( text="Dashboard экраны жок!", font_size=20 ) )
                    self.sm.add_widget ( dashboard )

            # Сатуу
            if not self.sm.has_screen ( 'sale' ):
                try:
                    from gui.screens.sale_screen import SaleScreen

                    sale = Screen ( name='sale' )
                    sale_widget = SaleScreen (
                        user_data=self.current_user_data,
                        product_manager=self.product_manager,
                        sales_manager=self.sales_manager,
                        on_back=lambda: self.navigate_to ( 'dashboard' )
                    )
                    sale.add_widget ( sale_widget )
                    self.sm.add_widget ( sale )
                    logger.info ( "Sale экраны түзүлдү" )
                except ImportError as e:
                    logger.error ( f"SaleScreen импорттоодо ката: {e}" )

            # Товарлар
            if not self.sm.has_screen ( 'products' ):
                try:
                    from gui.screens.product_screen import ProductScreen

                    products = Screen ( name='products' )
                    products_widget = ProductScreen (
                        user_data=self.current_user_data,
                        product_manager=self.product_manager,
                        on_back=lambda: self.navigate_to ( 'dashboard' )
                    )
                    products.add_widget ( products_widget )
                    self.sm.add_widget ( products )
                    logger.info ( "Products экраны түзүлдү" )
                except ImportError as e:
                    logger.error ( f"ProductScreen импорттоодо ката: {e}" )

            # Отчеттор
            if not self.sm.has_screen ( 'reports' ):
                try:
                    from gui.screens.report_screen import ReportScreen

                    reports = Screen ( name='reports' )
                    reports_widget = ReportScreen (
                        user_data=self.current_user_data,
                        report_manager=self.report_manager,
                        analytics_manager=self.analytics_manager,
                        on_back=lambda: self.navigate_to ( 'dashboard' )
                    )
                    reports.add_widget ( reports_widget )
                    self.sm.add_widget ( reports )
                    logger.info ( "Reports экраны түзүлдү" )
                except ImportError as e:
                    logger.error ( f"ReportScreen импорттоодо ката: {e}" )

            # Колдонуучулар (админ үчүн)
            if self.current_user_data['role'] == 'admin' and not self.sm.has_screen ( 'users' ):
                try:
                    from gui.screens.user_screen import UserScreen

                    users = Screen ( name='users' )
                    users_widget = UserScreen (
                        user_data=self.current_user_data,
                        auth_manager=self.auth_manager,
                        on_back=lambda: self.navigate_to ( 'dashboard' )
                    )
                    users.add_widget ( users_widget )
                    self.sm.add_widget ( users )
                    logger.info ( "Users экраны түзүлдү" )
                except ImportError as e:
                    logger.error ( f"UserScreen импорттоодо ката: {e}" )

            logger.info ( "Экрандар түзүлдү" )
        except Exception as e:
            logger.error ( f"Экрандарды түзүүдө ката: {e}" )
            import traceback
            traceback.print_exc ()

    def navigate_to(self, screen_name):
        if screen_name == 'logout':
            self.current_user_data = None
            self.sm.current = 'login'
        elif self.sm.has_screen ( screen_name ):
            self.sm.current = screen_name

    def on_stop(self):
        if self.db:
            self.db.close ()
        logger.info ( "Система токтотулду" )


if __name__ == '__main__':
    try:
        ShopSystemApp ().run ()
    except KeyboardInterrupt:
        logger.info ( "Колдонуучу тарабынан токтотулду" )
        sys.exit ( 0 )
    except Exception as e:
        logger.critical ( f"Күтүлбөгөн ката: {e}" )
        import traceback

        traceback.print_exc ()
        sys.exit ( 1 )