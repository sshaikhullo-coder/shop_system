from database.db_manager import DatabaseManager
from database.models import Product, Category, UnitType
from sqlalchemy.orm import joinedload
from datetime import datetime


class ProductManager:
    def __init__(self):
        self.db = DatabaseManager ()

    def get_session(self):
        return self.db.get_session ()

    def add_product(self, name, price, category_id, unit_type, stock=0, barcode=None, cost_price=0, min_stock=5):
        session = self.get_session ()
        try:
            product = Product (
                name=name,
                price=price,
                category_id=category_id,
                unit_type=UnitType ( unit_type ) if isinstance ( unit_type, str ) else unit_type,
                stock=stock,
                barcode=barcode,
                cost_price=cost_price,
                min_stock=min_stock
            )
            session.add ( product )
            session.commit ()
            return True, product
        except Exception as e:
            session.rollback ()
            return False, str ( e )
        finally:
            session.close ()

    def update_product(self, product_id, **kwargs):
        session = self.get_session ()
        try:
            product = session.query ( Product ).filter_by ( id=product_id ).first ()
            if product:
                for key, value in kwargs.items ():
                    if key == 'unit_type' and isinstance ( value, str ):
                        value = UnitType ( value )
                    if hasattr ( product, key ):
                        setattr ( product, key, value )
                session.commit ()
                return True, product
            return False, "Product not found"
        except Exception as e:
            session.rollback ()
            return False, str ( e )
        finally:
            session.close ()

    def delete_product(self, product_id):
        session = self.get_session ()
        try:
            product = session.query ( Product ).filter_by ( id=product_id ).first ()
            if product:
                product.is_active = False
                session.commit ()
                return True, "Deleted"
            return False, "Not found"
        except Exception as e:
            session.rollback ()
            return False, str ( e )
        finally:
            session.close ()

    def archive_product(self, product_id):
        """Товарды архивге жөнөтүү"""
        session = self.get_session ()
        try:
            product = session.query ( Product ).filter_by ( id=product_id ).first ()
            if product:
                product.is_active = False
                product.archived_at = datetime.now ()
                session.commit ()
                return True, "Товар архивге жөнөтүлдү"
            return False, "Товар табылган жок"
        except Exception as e:
            session.rollback ()
            return False, str ( e )
        finally:
            session.close ()

    def restore_product(self, product_id):
        """Архивден товарды калыбына келтирүү"""
        session = self.get_session ()
        try:
            product = session.query ( Product ).filter_by ( id=product_id ).first ()
            if product:
                product.is_active = True
                product.archived_at = None
                session.commit ()
                return True, "Товар калыбына келтирилди"
            return False, "Товар табылган жок"
        except Exception as e:
            session.rollback ()
            return False, str ( e )
        finally:
            session.close ()

    def get_all_products(self):
        session = self.get_session ()
        try:
            products = session.query ( Product ).options ( joinedload ( Product.category ) ).filter_by (
                is_active=True ).all ()
            return products
        finally:
            session.close ()

    def get_archived_products(self):
        """Архивдеги товарларды алуу"""
        session = self.get_session ()
        try:
            products = session.query ( Product ).options ( joinedload ( Product.category ) ).filter_by (
                is_active=False ).all ()
            return products
        finally:
            session.close ()


            

    def search_products(self, search_text):
        """Товарларды издөө (штрихкод же аты боюнча)"""
        session = self.get_session ()
        try:
            # Так штрихкод издөө
            if search_text.isdigit () or search_text.startswith ( 'TEST' ):
                # Штрихкод менен так издөө
                product = session.query ( Product ).options ( joinedload ( Product.category ) ).filter (
                    Product.barcode == search_text,
                    Product.is_active == True
                ).first ()
                if product:
                    return [product]

            # Аты боюнча издөө
            products = session.query ( Product ).options ( joinedload ( Product.category ) ).filter (
                Product.name.contains ( search_text ),
                Product.is_active == True
            ).all ()

            return products
        finally:
            session.close ()

    def update_stock(self, product_id, quantity):
        session = self.get_session ()
        try:
            product = session.query ( Product ).filter_by ( id=product_id ).first ()
            if product:
                product.stock += quantity
                session.commit ()
                return True, product.stock
            return False, "Not found"
        except Exception as e:
            session.rollback ()
            return False, str ( e )
        finally:
            session.close ()

    def get_low_stock_products(self):
        session = self.get_session ()
        try:
            products = session.query ( Product ).options ( joinedload ( Product.category ) ).filter (
                Product.stock <= Product.min_stock,
                Product.is_active == True
            ).all ()
            return products
        finally:
            session.close ()

    def add_category(self, name, description=""):
        session = self.get_session ()
        try:
            category = Category ( name=name, description=description )
            session.add ( category )
            session.commit ()
            return True, category
        except Exception as e:
            session.rollback ()
            return False, str ( e )
        finally:
            session.close ()

    def get_all_categories(self):
        session = self.get_session ()
        try:
            categories = session.query ( Category ).all ()
            return categories
        finally:
            session.close ()