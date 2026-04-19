"""
Менеджерлер модулу
"""

from managers.auth_manager import AuthManager
from managers.product_manager import ProductManager
from managers.sales_manager import SalesManager
from managers.analytics_manager import AnalyticsManager

__all__ = [
    'AuthManager',
    'ProductManager',
    'SalesManager',
    'AnalyticsManager'
]