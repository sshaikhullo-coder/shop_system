"""
Товарларды башкаруу менеджери
"""

from typing import List, Optional, Tuple
from database.db_manager import DatabaseManager
from database.models import Product, Category, UnitType


class ProductManager:
    """Товарлар менен иштөө"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    # ==================== КАТЕГОРИЯЛАР ====================

    def add_category(self, name: str) -> Tuple[bool, str]:
        """Жаңы категория кошуу"""
        if not name or not name.strip ():
            return False, "Категориянын атын киргизиңиз!"

        return self.db.add_category ( name.strip () )

    def get_all_categories(self) -> List[Category]:
        """Бардык категорияларды алуу"""
        return self.db.get_all_categories ()

    def get_category_by_id(self, category_id: int) -> Optional[Category]:
        """ID боюнча категория алуу"""
        return self.db.get_category_by_id ( category_id )

    def delete_category(self, category_id: int) -> Tuple[bool, str]:
        """Категорияны өчүрүү"""
        return self.db.delete_category ( category_id )

    # ==================== ТОВАРЛАР ====================

    def add_product(self, name: str, price: float, category_id: int,
                    unit_type: UnitType, stock: float = 0, barcode: str = None) -> Tuple[bool, str]:
        """Жаңы товар кошуу"""
        # Валидация
        if not name or not name.strip ():
            return False, "Товардын атын киргизиңиз!"

        if price <= 0:
            return False, "Баа 0дон чоң болушу керек!"

        if stock < 0:
            return False, "Сан терс болушу мүмкүн эмес!"

        category = self.get_category_by_id ( category_id )
        if not category:
            return False, "Категория табылган жок!"

        return self.db.add_product (
            name=name.strip (),
            price=price,
            category_id=category_id,
            unit_type=unit_type,
            stock=stock,
            barcode=barcode.strip () if barcode else None
        )

    def get_all_products(self) -> List[Product]:
        """Бардык активдүү товарларды алуу"""
        return self.db.get_all_products ( include_archived=False )

    def get_archived_products(self) -> List[Product]:
        """Архивдеги товарларды алуу"""
        return self.db.get_all_products ( include_archived=True )

    def get_product_by_id(self, product_id: int) -> Optional[Product]:
        """ID боюнча товар алуу"""
        return self.db.get_product_by_id ( product_id )

    def search_products(self, search_text: str) -> List[Product]:
        """Товарларды издөө"""
        if not search_text:
            return self.get_all_products ()
        return self.db.search_products ( search_text )

    def update_product(self, product_id: int, **kwargs) -> Tuple[bool, str]:
        """Товарды жаңыртуу"""
        # Валидация
        if 'price' in kwargs and kwargs['price'] <= 0:
            return False, "Баа 0дон чоң болушу керек!"

        if 'stock' in kwargs and kwargs['stock'] < 0:
            return False, "Сан терс болушу мүмкүн эмес!"

        if 'category_id' in kwargs and kwargs['category_id']:
            category = self.get_category_by_id ( kwargs['category_id'] )
            if not category:
                return False, "Категория табылган жок!"

        return self.db.update_product ( product_id, **kwargs )

    def update_stock(self, product_id: int, quantity: float) -> Tuple[bool, float]:
        """Товардын санын жаңыртуу"""
        product = self.get_product_by_id ( product_id )
        if not product:
            return False, "Товар табылган жок!"

        new_stock = product.stock + quantity
        if new_stock < 0:
            return False, "Складда жетишсиз товар!"

        return self.db.update_stock ( product_id, quantity )

    def archive_product(self, product_id: int) -> Tuple[bool, str]:
        """Товарды архивге жөнөтүү"""
        return self.db.archive_product ( product_id )

    def restore_product(self, product_id: int) -> Tuple[bool, str]:
        """Товарды калыбына келтирүү"""
        return self.db.restore_product ( product_id )

    def delete_product_permanent(self, product_id: int) -> Tuple[bool, str]:
        """Товарды толук өчүрүү"""
        return self.db.delete_product_permanent ( product_id )

    def get_low_stock_products(self, threshold: int = 10) -> List[Product]:
        """Төмөн складдагы товарларды алуу"""
        products = self.get_all_products ()
        return [p for p in products if p.stock <= threshold]