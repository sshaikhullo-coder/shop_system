"""
Сатууларды башкаруу менеджери
"""

from typing import List, Dict, Tuple, Optional
from datetime import datetime, timedelta
from database.db_manager import DatabaseManager
from managers.product_manager import ProductManager


class SalesManager:
    """Сатуулар менен иштөө"""

    def __init__(self, db_manager: DatabaseManager, product_manager: ProductManager):
        self.db = db_manager
        self.product_manager = product_manager
        self.current_sale = []

    def add_to_cart(self, product_id: int, quantity: float) -> Tuple[bool, str, Dict]:
        """Корзинага товар кошуу"""
        try:
            product = self.product_manager.get_product_by_id ( product_id )

            if not product:
                return False, "Товар табылган жок!", {}

            if not product.is_active:
                return False, "Бул товар архивде!", {}

            if quantity <= 0:
                return False, "Сан 0дон чоң болушу керек!", {}

            if product.stock < quantity:
                return False, f"Складда жетишсиз! (Бар: {product.stock} {product.unit_type.value})", {}

            # Корзинада барбы текшерүү
            for item in self.current_sale:
                if item['product_id'] == product_id:
                    new_quantity = item['quantity'] + quantity
                    if product.stock < new_quantity:
                        return False, f"Складда жетишсиз! (Бар: {product.stock} {product.unit_type.value})", {}

                    item['quantity'] = new_quantity
                    item['total'] = item['quantity'] * item['price']
                    return True, "Товардын саны көбөйтүлдү!", self.get_cart_summary ()

            # Жаңы товарды кошуу
            cart_item = {
                'product_id': product.id,
                'product_name': product.name,
                'quantity': quantity,
                'price': product.price,
                'total': quantity * product.price,
                'unit_type': product.unit_type.value,
                'stock': product.stock
            }
            self.current_sale.append ( cart_item )

            return True, "Товар корзинага кошулду!", self.get_cart_summary ()

        except Exception as e:
            return False, f"Ката: {str ( e )}", {}

    def remove_from_cart(self, product_id: int) -> Tuple[bool, str, Dict]:
        """Корзинадан товарды алып салуу"""
        try:
            for i, item in enumerate ( self.current_sale ):
                if item['product_id'] == product_id:
                    removed_item = self.current_sale.pop ( i )
                    return True, f"'{removed_item['product_name']}' корзинадан алынды!", self.get_cart_summary ()

            return False, "Товар корзинадан табылган жок!", self.get_cart_summary ()

        except Exception as e:
            return False, f"Ката: {str ( e )}", self.get_cart_summary ()

    def update_cart_quantity(self, product_id: int, quantity: float) -> Tuple[bool, str, Dict]:
        """Корзинадагы товардын санын өзгөртүү"""
        try:
            if quantity <= 0:
                return self.remove_from_cart ( product_id )

            for item in self.current_sale:
                if item['product_id'] == product_id:
                    product = self.product_manager.get_product_by_id ( product_id )
                    if product and product.stock < quantity:
                        return False, f"Складда жетишсиз! (Бар: {product.stock} {product.unit_type.value})", self.get_cart_summary ()

                    item['quantity'] = quantity
                    item['total'] = quantity * item['price']
                    return True, "Сан жаңыртылды!", self.get_cart_summary ()

            return False, "Товар корзинадан табылган жок!", self.get_cart_summary ()

        except Exception as e:
            return False, f"Ката: {str ( e )}", self.get_cart_summary ()

    def clear_cart(self) -> Dict:
        """Корзинаны тазалоо"""
        self.current_sale = []
        return self.get_cart_summary ()

    def get_cart_summary(self) -> Dict:
        """Корзинанын жыйынтыгын алуу"""
        total_items = len ( self.current_sale )
        total_quantity = sum ( item['quantity'] for item in self.current_sale )
        total_amount = sum ( item['total'] for item in self.current_sale )

        return {
            'items': self.current_sale.copy (),
            'total_items': total_items,
            'total_quantity': total_quantity,
            'total_amount': total_amount
        }

    def process_sale(self, user_id: int, payment_amount: float,
                     payment_method: str, notes: str = "") -> Tuple[bool, str, Dict]:
        """Сатууну аяктоо"""
        try:
            if not self.current_sale:
                return False, "Корзина бош!", {}

            cart_summary = self.get_cart_summary ()

            if payment_amount < cart_summary['total_amount']:
                return False, "Төлөм суммасы жетишсиз!", {}

            # Сатууну түзүү
            sale_items = []
            for item in self.current_sale:
                sale_items.append ( {
                    'product_id': item['product_id'],
                    'quantity': item['quantity'],
                    'price': item['price'],
                    'total': item['total']
                } )

            success, result = self.db.create_sale (
                user_id=user_id,
                items=sale_items,
                payment_amount=payment_amount,
                payment_method=payment_method,
                notes=notes
            )

            if success:
                # Корзинаны тазалоо
                self.clear_cart ()
                return True, "Сатуу ийгиликтүү аяктады!", result

            return False, result, {}

        except Exception as e:
            return False, f"Сатуу катасы: {str ( e )}", {}

    def get_sales_history(self, days: int = 30) -> List[Dict]:
        """Сатуулардын тарыхын алуу"""
        end_date = datetime.now ()
        start_date = end_date - timedelta ( days=days )

        sales = self.db.get_sales (
            start_date=start_date.strftime ( '%Y-%m-%d' ),
            end_date=end_date.strftime ( '%Y-%m-%d' )
        )

        return [sale.__dict__ for sale in sales]

    def get_sale_by_id(self, sale_id: int) -> Optional[Dict]:
        """ID боюнча сатуу алуу"""
        sale = self.db.get_sale_by_id ( sale_id )
        return sale.__dict__ if sale else None

    def get_today_sales(self) -> Dict:
        """Бүгүнкү сатууларды алуу"""
        today = datetime.now ().strftime ( '%Y-%m-%d' )
        sales = self.db.get_sales ( start_date=today, end_date=today )

        total_amount = sum ( sale.total_amount for sale in sales )
        total_count = len ( sales )

        return {
            'date': today,
            'total_amount': total_amount,
            'sales_count': total_count,
            'avg_check': total_amount / total_count if total_count > 0 else 0
        }