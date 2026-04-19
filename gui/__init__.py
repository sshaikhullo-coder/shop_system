"""
GUI модулу
"""

from gui.screens.login_screen import LoginScreen
from gui.screens.dashboard_screen import DashboardScreen
from gui.screens.products_screen import ProductScreen
from gui.screens.sale_screen import SaleScreen
from gui.screens.reports_screen import ReportsScreen
from gui.screens.users_screen import UsersScreen

__all__ = [
    'LoginScreen',
    'DashboardScreen',
    'ProductScreen',
    'SaleScreen',
    'ReportsScreen',
    'UsersScreen'
]