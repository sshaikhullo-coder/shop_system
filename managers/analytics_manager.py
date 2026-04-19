"""
Аналитика жана отчеттор менеджери
"""

from typing import List, Dict
from datetime import datetime, timedelta
from database.db_manager import DatabaseManager


class AnalyticsManager:
    """Аналитика жана отчеттор"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def get_daily_report(self, date: str = None) -> Dict:
        """Күндүк отчет алуу"""
        return self.db.get_daily_sales ( date )

    def get_weekly_report(self) -> Dict:
        """Жумалык отчет алуу"""
        reports = []
        total_amount = 0
        total_sales = 0

        for i in range ( 7 ):
            date = (datetime.now () - timedelta ( days=i )).strftime ( '%Y-%m-%d' )
            report = self.get_daily_report ( date )
            reports.append ( report )
            total_amount += report['total_amount']
            total_sales += report['sales_count']

        return {
            'period': 'weekly',
            'reports': reports,
            'total_amount': total_amount,
            'total_sales': total_sales,
            'avg_daily': total_amount / 7 if total_sales > 0 else 0
        }

    def get_monthly_report(self) -> Dict:
        """Айлык отчет алуу"""
        reports = []
        total_amount = 0
        total_sales = 0

        for i in range ( 30 ):
            date = (datetime.now () - timedelta ( days=i )).strftime ( '%Y-%m-%d' )
            report = self.get_daily_report ( date )
            reports.append ( report )
            total_amount += report['total_amount']
            total_sales += report['sales_count']

        return {
            'period': 'monthly',
            'reports': reports,
            'total_amount': total_amount,
            'total_sales': total_sales,
            'avg_daily': total_amount / 30 if total_sales > 0 else 0
        }

    def get_top_products(self, limit: int = 10, days: int = 30) -> List[Dict]:
        """Эң көп сатылган товарлар"""
        return self.db.get_top_products ( limit, days )

    def get_sales_by_hour(self, date: str = None) -> List[Dict]:
        """Сааттар боюнча сатуу статистикасы"""
        if not date:
            date = datetime.now ().strftime ( '%Y-%m-%d' )

        sales = self.db.get_sales ( start_date=date, end_date=date )

        hourly_sales = {}
        for hour in range ( 24 ):
            hourly_sales[hour] = {'count': 0, 'amount': 0}

        for sale in sales:
            hour = sale.sale_date.hour
            hourly_sales[hour]['count'] += 1
            hourly_sales[hour]['amount'] += sale.total_amount

        return [{'hour': h, **data} for h, data in hourly_sales.items ()]

    def get_payment_method_stats(self, days: int = 30) -> List[Dict]:
        """Төлөм ыкмалары боюнча статистика"""
        end_date = datetime.now ()
        start_date = end_date - timedelta ( days=days )

        sales = self.db.get_sales (
            start_date=start_date.strftime ( '%Y-%m-%d' ),
            end_date=end_date.strftime ( '%Y-%m-%d' )
        )

        stats = {}
        for sale in sales:
            method = sale.payment_method
            if method not in stats:
                stats[method] = {'count': 0, 'amount': 0}
            stats[method]['count'] += 1
            stats[method]['amount'] += sale.total_amount

        return [{'method': k, **v} for k, v in stats.items ()]

    def get_profit_analysis(self, days: int = 30) -> Dict:
        """Пайда анализи (орточо баа боюнча)"""
        sales = self.db.get_sales (
            start_date=(datetime.now () - timedelta ( days=days )).strftime ( '%Y-%m-%d' ),
            end_date=datetime.now ().strftime ( '%Y-%m-%d' )
        )

        total_revenue = sum ( sale.total_amount for sale in sales )

        # Орточо пайда 20% деп эсептейбиз
        estimated_profit = total_revenue * 0.2

        return {
            'period_days': days,
            'total_revenue': total_revenue,
            'estimated_profit': estimated_profit,
            'profit_margin': 20
        }

    def get_inventory_value(self) -> float:
        """Складдагы товарлардын жалпы баасы"""
        products = self.db.get_all_products ( include_archived=False )
        total_value = sum ( p.price * p.stock for p in products )
        return total_value