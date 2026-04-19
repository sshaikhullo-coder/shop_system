from database.db_manager import DatabaseManager
from database.models import ReturnedProduct, Product, Sale
from datetime import datetime
from sqlalchemy import func


class ReturnManager:
    def __init__(self):
        self.db = DatabaseManager ()

    def get_session(self):
        return self.db.get_session ()

    def return_product(self, sale_id, product_id, quantity, reason=""):
        """Товарды кайтаруу"""
        session = self.get_session ()
        try:
            sale = session.query ( Sale ).filter_by ( id=sale_id ).first ()
            if not sale:
                return False, "Сатуу табылган жок"

            product = session.query ( Product ).filter_by ( id=product_id ).first ()
            if not product:
                return False, "Товар табылган жок"

            # Сатуудагы товардын баасын алуу
            from database.models import SaleItem
            sale_item = session.query ( SaleItem ).filter_by ( sale_id=sale_id, product_id=product_id ).first ()
            if not sale_item:
                return False, "Бул сатууда мындай товар жок"

            returned = ReturnedProduct (
                sale_id=sale_id,
                product_id=product_id,
                product_name=product.name,
                barcode=product.barcode,
                quantity=quantity,
                return_price=sale_item.price,
                reason=reason
            )
            session.add ( returned )

            # Складга кошуу
            product.stock += quantity

            session.commit ()
            return True, f"{quantity} даана товар кайтарылды"
        except Exception as e:
            session.rollback ()
            return False, str ( e )
        finally:
            session.close ()

    def get_returns(self, start_date=None, end_date=None):
        """Кайтарылган товарларды алуу"""
        session = self.get_session ()
        try:
            query = session.query ( ReturnedProduct ).order_by ( ReturnedProduct.return_date.desc () )

            if start_date:
                query = query.filter ( ReturnedProduct.return_date >= start_date )
            if end_date:
                query = query.filter ( ReturnedProduct.return_date <= end_date )

            return query.all ()
        finally:
            session.close ()

    def get_total_return_amount(self, start_date=None, end_date=None):
        """Кайтарылган товарлардын жалпы суммасы"""
        session = self.get_session ()
        try:
            query = session.query ( func.sum ( ReturnedProduct.return_price * ReturnedProduct.quantity ) )

            if start_date:
                query = query.filter ( ReturnedProduct.return_date >= start_date )
            if end_date:
                query = query.filter ( ReturnedProduct.return_date <= end_date )

            total = query.scalar () or 0
            return total
        finally:
            session.close ()