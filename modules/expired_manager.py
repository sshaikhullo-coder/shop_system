from database.db_manager import DatabaseManager
from database.models import ExpiredProduct, Product
from datetime import datetime, timedelta
from sqlalchemy import func


class ExpiredManager:
    def __init__(self):
        self.db = DatabaseManager ()

    def get_session(self):
        return self.db.get_session ()

    def add_expired_product(self, product_id, expiry_date, quantity, notes=""):
        """Мөөнөтү өткөн товарды кошуу"""
        session = self.get_session ()
        try:
            product = session.query ( Product ).filter_by ( id=product_id ).first ()
            if not product:
                return False, "Товар табылган жок"

            expired = ExpiredProduct (
                product_id=product_id,
                product_name=product.name,
                barcode=product.barcode,
                expiry_date=expiry_date,
                quantity=quantity,
                notes=notes
            )
            session.add ( expired )

            # Складдан азайтуу
            product.stock -= quantity

            session.commit ()
            return True, "Мөөнөтү өткөн товар кошулду"
        except Exception as e:
            session.rollback ()
            return False, str ( e )
        finally:
            session.close ()

    def get_expired_products(self, status="active"):
        """Мөөнөтү өткөн товарларды алуу"""
        session = self.get_session ()
        try:
            expired = session.query ( ExpiredProduct ).filter_by ( status=status ).order_by (
                ExpiredProduct.expiry_date ).all ()
            return expired
        finally:
            session.close ()

    def get_near_expiry_products(self, days=7):
        """Жакын арада мөөнөтү бүтө турган товарлар"""
        session = self.get_session ()
        try:
            today = datetime.now ().date ()
            future = today + timedelta ( days=days )

            products = session.query ( Product ).filter (
                Product.expiry_date <= future,
                Product.expiry_date >= today,
                Product.stock > 0
            ).all ()
            return products
        finally:
            session.close ()

    def mark_as_processed(self, expired_id):
        """Мөөнөтү өткөн товарды иштетилди деп белгилөө"""
        session = self.get_session ()
        try:
            expired = session.query ( ExpiredProduct ).filter_by ( id=expired_id ).first ()
            if expired:
                expired.status = "processed"
                session.commit ()
                return True, "Белгиленди"
            return False, "Табылган жок"
        except Exception as e:
            session.rollback ()
            return False, str ( e )
        finally:
            session.close ()