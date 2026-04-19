from database.db_manager import DatabaseManager
from database.models import Sale, SaleItem, Product
from datetime import datetime, timedelta
from sqlalchemy import func


class AnalyticsManager:
    def __init__(self):
        self.db = DatabaseManager ()

    def get_session(self):
        return self.db.get_session ()

    def get_top_products(self, limit=5, days=30):
        session = self.get_session ()
        try:
            start_date = datetime.now () - timedelta ( days=days )

            results = session.query (
                Product.name,
                func.sum ( SaleItem.quantity ).label ( 'total_quantity' ),
                func.sum ( SaleItem.total ).label ( 'total_amount' )
            ).join ( SaleItem, SaleItem.product_id == Product.id ) \
                .join ( Sale, Sale.id == SaleItem.sale_id ) \
                .filter ( Sale.created_at >= start_date ) \
                .group_by ( Product.id ) \
                .order_by ( func.sum ( SaleItem.total ).desc () ) \
                .limit ( limit ).all ()
            return results
        finally:
            session.close ()