# modules/sales_history.py
from database.db_manager import DatabaseManager
from database.models import Sale, SaleItem, Product, User
from datetime import datetime, timedelta
from sqlalchemy import func, and_


class SalesHistory:
    def __init__(self):
        self.db = DatabaseManager ()

    def get_sales_history(self, start_date=None, end_date=None, user_id=None):
        """Сатуу тарыхын алуу"""
        session = self.db.get_session ()
        try:
            query = session.query (
                Sale.id,
                Sale.sale_number,
                Sale.created_at,
                User.username.label ( 'cashier' ),
                Sale.total_amount,
                Sale.payment_type
            ).join ( User, User.id == Sale.user_id )

            if start_date:
                query = query.filter ( Sale.created_at >= start_date )
            if end_date:
                query = query.filter ( Sale.created_at <= end_date )
            if user_id:
                query = query.filter ( Sale.user_id == user_id )

            sales = query.order_by ( Sale.created_at.desc () ).all ()

            result = []
            for sale in sales:
                items = session.query (
                    Product.name,
                    SaleItem.quantity,
                    SaleItem.price,
                    SaleItem.total
                ).join ( SaleItem, SaleItem.product_id == Product.id ) \
                    .filter ( SaleItem.sale_id == sale.id ).all ()

                result.append ( {
                    'id': sale.id,
                    'sale_number': sale.sale_number,
                    'date': sale.created_at,
                    'cashier': sale.cashier,
                    'total': sale.total_amount,
                    'payment_type': sale.payment_type.value,
                    'items': [{'name': i[0], 'quantity': i[1], 'price': i[2], 'total': i[3]} for i in items]
                } )

            return result
        finally:
            session.close ()

    def get_today_sales_detail(self):
        """Бүгүнкү сатуулардын деталдуу тизмеси"""
        today = datetime.now ().date ()
        return self.get_sales_history ( start_date=today, end_date=today + timedelta ( days=1 ) )