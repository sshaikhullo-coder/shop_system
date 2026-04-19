from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.core.window import Window
from kivy.lang import Builder
import os

# Set window size for desktop
Window.size = (1200, 800)


class LoginScreen ( Screen ):
    pass


class DashboardScreen ( Screen ):
    pass


class SaleScreen ( Screen ):
    pass


class ProductScreen ( Screen ):
    pass


class ReportScreen ( Screen ):
    pass


class UserScreen ( Screen ):
    pass


class ShopApp ( App ):
    def __init__(self, **kwargs):
        super ().__init__ ( **kwargs )
        self.db_manager = None
        self.current_user = None

    def build(self):
        # Load KV files
        kv_path = os.path.join ( os.path.dirname ( __file__ ), 'screens' )

        # Create screen manager
        sm = ScreenManager ()

        # Add screens
        sm.add_widget ( LoginScreen ( name='login' ) )
        sm.add_widget ( DashboardScreen ( name='dashboard' ) )
        sm.add_widget ( SaleScreen ( name='sale' ) )
        sm.add_widget ( ProductScreen ( name='product' ) )
        sm.add_widget ( ReportScreen ( name='report' ) )
        sm.add_widget ( UserScreen ( name='user' ) )

        return sm

    def on_start(self):
        # Initialize database on start
        from database.db_manager import DatabaseManager
        self.db_manager = DatabaseManager ()

    def on_stop(self):
        # Close database connection
        if self.db_manager:
            self.db_manager.close ()


if __name__ == '__main__':
    ShopApp ().run ()