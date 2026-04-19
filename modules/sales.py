from database.db_manager import DatabaseManager
from database.models import Sale, SaleItem, Product, PaymentType
from datetime import datetime
import uuid


class SalesManager:
    def __init__(self):
        self.db = DatabaseManager ()
        self.current_cart = []
        self.on_sale_complete = None

    def get_session(self):
        return self.db.get_session ()

    def add_to_cart(self, product, quantity):
        if quantity <= 0:
            return False, "Сан туура эмес"
        if product.stock < quantity:
            return False, f"Складда жетишсиз: {product.stock} {product.unit_type.value}"

        cart_item = {
            'product': product,
            'quantity': quantity,
            'price': product.price,
            'total': product.price * quantity
        }
        self.current_cart.append ( cart_item )
        return True, "Кошулду"

    def remove_from_cart(self, index):
        if 0 <= index < len ( self.current_cart ):
            self.current_cart.pop ( index )
            return True
        return False

    def clear_cart(self):
        self.current_cart = []

    def get_cart_total(self):
        return sum ( item['total'] for item in self.current_cart )

    def get_cart_items(self):
        return self.current_cart

    def create_sale(self, user_id, payment_type, paid_amount, notes=""):
        if not self.current_cart:
            return False, "Корзина бош"

        total = self.get_cart_total ()
        if paid_amount < total and payment_type != PaymentType.CREDIT:
            return False, f"Төлөнүүчү сумма жетишсиз. Керек: {total}"

        change = paid_amount - total if paid_amount > total else 0

        session = self.get_session ()
        try:
            sale_number = f"INV-{datetime.now ().strftime ( '%Y%m%d%H%M%S' )}-{uuid.uuid4 ().hex[:4].upper ()}"

            sale = Sale (
                sale_number=sale_number,
                user_id=user_id,
                payment_type=payment_type,
                total_amount=total,
                paid_amount=paid_amount,
                change_amount=change,
                notes=notes
            )
            session.add ( sale )
            session.flush ()

            items_copy = []
            for item in self.current_cart:
                product = item['product']
                current_product = session.query ( Product ).filter_by ( id=product.id ).first ()

                if current_product.stock < item['quantity']:
                    raise Exception ( f"{current_product.name} товарынын запасы жетишсиз!" )

                sale_item = SaleItem (
                    sale_id=sale.id,
                    product_id=product.id,
                    quantity=item['quantity'],
                    price=item['price'],
                    total=item['total']
                )
                session.add ( sale_item )

                current_product.stock -= item['quantity']

                items_copy.append ( {
                    'product_name': product.name,
                    'product_unit': product.unit_type.value,
                    'quantity': item['quantity'],
                    'price': item['price'],
                    'total': item['total']
                } )

            session.commit ()

            sale_result = {
                'sale': {
                    'id': sale.id,
                    'sale_number': sale.sale_number,
                    'total_amount': sale.total_amount,
                    'paid_amount': sale.paid_amount,
                    'change_amount': sale.change_amount,
                    'created_at': sale.created_at
                },
                'items': items_copy,
                'change': change
            }

            self.clear_cart ()

            if self.on_sale_complete:
                self.on_sale_complete ( sale_result )

            return True, sale_result

        except Exception as e:
            session.rollback ()
            return False, str ( e )
        finally:
            session.close ()

    def get_today_sales(self):
        session = self.get_session ()
        try:
            today = datetime.now ().date ()
            sales = session.query ( Sale ).filter (
                Sale.created_at >= today,
                Sale.created_at < today.replace ( day=today.day + 1 )
            ).all ()

            sales_data = []
            for sale in sales:
                sales_data.append ( {
                    'id': sale.id,
                    'sale_number': sale.sale_number,
                    'total_amount': sale.total_amount,
                    'created_at': sale.created_at,
                    'payment_type': sale.payment_type
                } )
            return sales_data
        finally:
            session.close ()

    def get_sales_by_date(self, start_date, end_date):
        """Берилген дата диапазонундагы сатууларды алуу"""
        session = self.get_session ()
        try:
            from database.models import Sale, SaleItem, Product

            # Даталарды тууралоо
            if isinstance ( start_date, datetime ):
                start = start_date
            else:
                start = datetime ( start_date.year, start_date.month, start_date.day, 0, 0, 0 )

            if isinstance ( end_date, datetime ):
                end = end_date
            else:
                end = datetime ( end_date.year, end_date.month, end_date.day, 23, 59, 59 )

            sales = session.query ( Sale ).filter (
                Sale.created_at >= start,
                Sale.created_at <= end
            ).order_by ( Sale.created_at.desc () ).all ()

            # Сатуулардын тизмесин даярдоо
            sales_data = []
            for sale in sales:
                items = session.query ( SaleItem ).filter ( SaleItem.sale_id == sale.id ).all ()
                sale_items = []
                for item in items:
                    product = session.query ( Product ).filter ( Product.id == item.product_id ).first ()
                    sale_items.append ( {
                        'product': product,
                        'quantity': item.quantity,
                        'price': item.price,
                        'total': item.total
                    } )

                sales_data.append ( {
                    'id': sale.id,
                    'sale_number': sale.sale_number,
                    'created_at': sale.created_at,
                    'total_amount': sale.total_amount,
                    'paid_amount': sale.paid_amount,
                    'payment_type': sale.payment_type,
                    'items': sale_items,
                    'user_id': sale.user_id
                } )

            return sales_data
        finally:
            session.close ()