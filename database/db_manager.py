"""
Маалымат базасын башкаруу модулу
"""

import sqlite3
import os
from datetime import datetime
from typing import List, Optional, Dict, Any
from contextlib import contextmanager

from database.models import User, Product, Category, Sale, SaleItem, UnitType


class DatabaseManager:
    """Маалымат базасын башкаруу классы"""

    def __init__(self, db_path: str = "shop_system.db"):
        self.db_path = db_path
        # Эски маалымат базасын өчүрүү (эгер бар болсо)
        if os.path.exists ( db_path ):
            try:
                os.remove ( db_path )
                print ( f"✅ Эски маалымат базасы өчүрүлдү: {db_path}" )
            except:
                pass
        self.init_database ()

    @contextmanager
    def get_connection(self):
        """Маалымат базасына байланыш алуу"""
        conn = sqlite3.connect ( self.db_path )
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit ()
        except Exception as e:
            conn.rollback ()
            raise e
        finally:
            conn.close ()

    def init_database(self):
        """Маалымат базасын түзүү"""
        with self.get_connection () as conn:
            cursor = conn.cursor ()

            # Категориялар таблицасы
            cursor.execute ( """
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """ )

            # Товарлар таблицасы
            cursor.execute ( """
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    price REAL NOT NULL,
                    stock REAL NOT NULL DEFAULT 0,
                    unit_type TEXT NOT NULL DEFAULT 'даана',
                    barcode TEXT UNIQUE,
                    category_id INTEGER,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (category_id) REFERENCES categories (id) ON DELETE SET NULL
                )
            """ )

            # Колдонуучулар таблицасы
            cursor.execute ( """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    full_name TEXT NOT NULL,
                    role TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP
                )
            """ )

            # Сатуулар таблицасы - ТҮЗӨТҮЛДҮ (sale_date ордуна created_at)
            cursor.execute ( """
                CREATE TABLE IF NOT EXISTS sales (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    invoice_number TEXT UNIQUE NOT NULL,
                    user_id INTEGER NOT NULL,
                    total_amount REAL NOT NULL,
                    payment_amount REAL NOT NULL,
                    change_amount REAL NOT NULL,
                    payment_method TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    notes TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """ )

            # Сатуу элементтери таблицасы
            cursor.execute ( """
                CREATE TABLE IF NOT EXISTS sale_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sale_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    quantity REAL NOT NULL,
                    price REAL NOT NULL,
                    total REAL NOT NULL,
                    FOREIGN KEY (sale_id) REFERENCES sales (id) ON DELETE CASCADE,
                    FOREIGN KEY (product_id) REFERENCES products (id)
                )
            """ )

            # Индекстерди түзүү - ТҮЗӨТҮЛДҮ
            cursor.execute ( "CREATE INDEX IF NOT EXISTS idx_products_name ON products(name)" )
            cursor.execute ( "CREATE INDEX IF NOT EXISTS idx_products_barcode ON products(barcode)" )
            cursor.execute ( "CREATE INDEX IF NOT EXISTS idx_sales_created_at ON sales(created_at)" )
            cursor.execute ( "CREATE INDEX IF NOT EXISTS idx_sales_invoice ON sales(invoice_number)" )
            cursor.execute ( "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)" )

            # Триггерлерди түзүү
            cursor.execute ( """
                CREATE TRIGGER IF NOT EXISTS update_products_timestamp 
                AFTER UPDATE ON products
                BEGIN
                    UPDATE products SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
                END
            """ )

            # Баштапкы категорияларды кошуу
            cursor.execute ( "INSERT OR IGNORE INTO categories (name) VALUES (?)", ("Жалпы",) )
            cursor.execute ( "INSERT OR IGNORE INTO categories (name) VALUES (?)", ("Азык-түлүк",) )
            cursor.execute ( "INSERT OR IGNORE INTO categories (name) VALUES (?)", ("Суусундуктар",) )

            print ( "✅ Маалымат базасы ийгиликтүү түзүлдү!" )

    # ==================== КАТЕГОРИЯЛАР ====================

    def add_category(self, name: str) -> tuple:
        """Жаңы категория кошуу"""
        try:
            with self.get_connection () as conn:
                cursor = conn.cursor ()
                cursor.execute ( "INSERT INTO categories (name) VALUES (?)", (name,) )
                return True, cursor.lastrowid
        except sqlite3.IntegrityError:
            return False, "Бул категория мурунтан бар!"
        except Exception as e:
            return False, str ( e )

    def get_all_categories(self) -> List[Category]:
        """Бардык категорияларды алуу"""
        with self.get_connection () as conn:
            cursor = conn.cursor ()
            cursor.execute ( "SELECT * FROM categories ORDER BY name" )
            rows = cursor.fetchall ()
            return [Category ( **dict ( row ) ) for row in rows]

    def get_category_by_id(self, category_id: int) -> Optional[Category]:
        """ID боюнча категория алуу"""
        with self.get_connection () as conn:
            cursor = conn.cursor ()
            cursor.execute ( "SELECT * FROM categories WHERE id = ?", (category_id,) )
            row = cursor.fetchone ()
            return Category ( **dict ( row ) ) if row else None

    def delete_category(self, category_id: int) -> tuple:
        """Категорияны өчүрүү"""
        try:
            with self.get_connection () as conn:
                cursor = conn.cursor ()
                # Категорияда товар барбы текшерүү
                cursor.execute ( "SELECT COUNT(*) FROM products WHERE category_id = ?", (category_id,) )
                count = cursor.fetchone ()[0]
                if count > 0:
                    return False, f"Бул категорияда {count} товар бар. Аларды башка категорияга өткөрүңүз!"

                cursor.execute ( "DELETE FROM categories WHERE id = ?", (category_id,) )
                return True, "Категория өчүрүлдү!"
        except Exception as e:
            return False, str ( e )

    # ==================== ТОВАРЛАР ====================

    def add_product(self, name: str, price: float, category_id: int,
                    unit_type: UnitType, stock: float = 0, barcode: str = None) -> tuple:
        """Жаңы товар кошуу"""
        try:
            with self.get_connection () as conn:
                cursor = conn.cursor ()
                cursor.execute ( """
                    INSERT INTO products (name, price, stock, unit_type, barcode, category_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (name, price, stock, unit_type.value, barcode, category_id) )
                return True, cursor.lastrowid
        except sqlite3.IntegrityError:
            return False, "Бул штрихкод менен товар мурунтан бар!"
        except Exception as e:
            return False, str ( e )

    def get_all_products(self, include_archived: bool = False) -> List[Product]:
        """Бардык товарларды алуу"""
        with self.get_connection () as conn:
            cursor = conn.cursor ()
            if include_archived:
                cursor.execute ( """
                    SELECT p.*, c.name as category_name 
                    FROM products p
                    LEFT JOIN categories c ON p.category_id = c.id
                    ORDER BY p.name
                """ )
            else:
                cursor.execute ( """
                    SELECT p.*, c.name as category_name 
                    FROM products p
                    LEFT JOIN categories c ON p.category_id = c.id
                    WHERE p.is_active = 1
                    ORDER BY p.name
                """ )
            rows = cursor.fetchall ()
            products = []
            for row in rows:
                data = dict ( row )
                category = Category ( id=data.pop ( 'category_id' ), name=data.pop ( 'category_name' ) ) if data.get (
                    'category_id' ) else None
                products.append ( Product ( **data, category=category ) )
            return products

    def get_product_by_id(self, product_id: int) -> Optional[Product]:
        """ID боюнча товар алуу"""
        with self.get_connection () as conn:
            cursor = conn.cursor ()
            cursor.execute ( """
                SELECT p.*, c.name as category_name 
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
                WHERE p.id = ?
            """, (product_id,) )
            row = cursor.fetchone ()
            if row:
                data = dict ( row )
                category = Category ( id=data.pop ( 'category_id' ), name=data.pop ( 'category_name' ) ) if data.get (
                    'category_id' ) else None
                return Product ( **data, category=category )
            return None

    def update_product(self, product_id: int, **kwargs) -> tuple:
        """Товарды жаңыртуу"""
        try:
            with self.get_connection () as conn:
                cursor = conn.cursor ()
                allowed_fields = ['name', 'price', 'stock', 'unit_type', 'barcode', 'category_id', 'is_active']
                updates = []
                values = []

                for key, value in kwargs.items ():
                    if key in allowed_fields and value is not None:
                        updates.append ( f"{key} = ?" )
                        values.append ( value )

                if not updates:
                    return False, "Өзгөртүү жок!"

                values.append ( product_id )
                query = f"UPDATE products SET {', '.join ( updates )} WHERE id = ?"
                cursor.execute ( query, values )
                return True, "Товар жаңыртылды!"
        except Exception as e:
            return False, str ( e )

    def update_stock(self, product_id: int, quantity: float) -> tuple:
        """Товардын санын жаңыртуу"""
        try:
            with self.get_connection () as conn:
                cursor = conn.cursor ()
                cursor.execute ( "UPDATE products SET stock = stock + ? WHERE id = ?", (quantity, product_id) )
                cursor.execute ( "SELECT stock FROM products WHERE id = ?", (product_id,) )
                new_stock = cursor.fetchone ()[0]
                return True, new_stock
        except Exception as e:
            return False, str ( e )

    def search_products(self, search_text: str) -> List[Product]:
        """Товарларды издөө"""
        with self.get_connection () as conn:
            cursor = conn.cursor ()
            search_pattern = f"%{search_text}%"
            cursor.execute ( """
                SELECT p.*, c.name as category_name 
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
                WHERE p.is_active = 1 AND (
                    p.name LIKE ? OR 
                    p.barcode LIKE ? OR 
                    c.name LIKE ?
                )
                ORDER BY p.name
            """, (search_pattern, search_pattern, search_pattern) )
            rows = cursor.fetchall ()
            products = []
            for row in rows:
                data = dict ( row )
                category = Category ( id=data.pop ( 'category_id' ), name=data.pop ( 'category_name' ) ) if data.get (
                    'category_id' ) else None
                products.append ( Product ( **data, category=category ) )
            return products

    def archive_product(self, product_id: int) -> tuple:
        """Товарды архивге жөнөтүү"""
        return self.update_product ( product_id, is_active=False )

    def restore_product(self, product_id: int) -> tuple:
        """Товарды калыбына келтирүү"""
        return self.update_product ( product_id, is_active=True )

    def delete_product_permanent(self, product_id: int) -> tuple:
        """Товарды толук өчүрүү"""
        try:
            with self.get_connection () as conn:
                cursor = conn.cursor ()
                # Сатуу элементтерин текшерүү
                cursor.execute ( "SELECT COUNT(*) FROM sale_items WHERE product_id = ?", (product_id,) )
                count = cursor.fetchone ()[0]
                if count > 0:
                    return False, f"Бул товар {count} сатууда колдонулган. Адегенде сатууларды өчүрүңүз!"

                cursor.execute ( "DELETE FROM products WHERE id = ?", (product_id,) )
                return True, "Товар толугу менен өчүрүлдү!"
        except Exception as e:
            return False, str ( e )

    # ==================== КОЛДОНУУЧУЛАР ====================

    def add_user(self, username: str, password: str, full_name: str, role: str) -> tuple:
        """Жаңы колдонуучу кошуу"""
        try:
            with self.get_connection () as conn:
                cursor = conn.cursor ()
                cursor.execute ( """
                    INSERT INTO users (username, password, full_name, role)
                    VALUES (?, ?, ?, ?)
                """, (username, password, full_name, role) )
                return True, cursor.lastrowid
        except sqlite3.IntegrityError:
            return False, "Бул колдонуучу аты мурунтан бар!"
        except Exception as e:
            return False, str ( e )

    def get_user_by_username(self, username: str) -> Optional[User]:
        """Колдонуучу аты боюнча колдонуучу алуу"""
        with self.get_connection () as conn:
            cursor = conn.cursor ()
            cursor.execute ( "SELECT * FROM users WHERE username = ? AND is_active = 1", (username,) )
            row = cursor.fetchone ()
            return User ( **dict ( row ) ) if row else None

    def get_all_users(self) -> List[User]:
        """Бардык колдонуучуларды алуу"""
        with self.get_connection () as conn:
            cursor = conn.cursor ()
            cursor.execute ( "SELECT * FROM users ORDER BY username" )
            rows = cursor.fetchall ()
            return [User ( **dict ( row ) ) for row in rows]

    def update_user(self, user_id: int, **kwargs) -> tuple:
        """Колдонуучуну жаңыртуу"""
        try:
            with self.get_connection () as conn:
                cursor = conn.cursor ()
                allowed_fields = ['full_name', 'role', 'is_active', 'password']
                updates = []
                values = []

                for key, value in kwargs.items ():
                    if key in allowed_fields and value is not None:
                        updates.append ( f"{key} = ?" )
                        values.append ( value )

                if not updates:
                    return False, "Өзгөртүү жок!"

                values.append ( user_id )
                query = f"UPDATE users SET {', '.join ( updates )} WHERE id = ?"
                cursor.execute ( query, values )
                return True, "Колдонуучу жаңыртылды!"
        except Exception as e:
            return False, str ( e )

    def update_last_login(self, user_id: int):
        """Акыркы кирүү убактысын жаңыртуу"""
        with self.get_connection () as conn:
            cursor = conn.cursor ()
            cursor.execute ( "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?", (user_id,) )

    def delete_user(self, user_id: int) -> tuple:
        """Колдонуучуну өчүрүү"""
        try:
            with self.get_connection () as conn:
                cursor = conn.cursor ()
                # Администраторду өчүрбөө
                cursor.execute ( "SELECT role FROM users WHERE id = ?", (user_id,) )
                row = cursor.fetchone ()
                if row and row[0] == 'admin':
                    return False, "Администраторду өчүрүү мүмкүн эмес!"

                cursor.execute ( "DELETE FROM users WHERE id = ?", (user_id,) )
                return True, "Колдонуучу өчүрүлдү!"
        except Exception as e:
            return False, str ( e )

    # ==================== САТУУЛАР ====================

    def create_sale(self, user_id: int, items: List[Dict], payment_amount: float,
                    payment_method: str, notes: str = "") -> tuple:
        """Сатуу түзүү"""
        try:
            with self.get_connection () as conn:
                cursor = conn.cursor ()

                # Жалпы сумманы эсептөө
                total_amount = sum ( item['total'] for item in items )
                change_amount = payment_amount - total_amount

                if change_amount < 0:
                    return False, "Төлөм суммасы жетишсиз!"

                # Уникалдуу чек номерин түзүү
                invoice_number = f"INV-{datetime.now ().strftime ( '%Y%m%d-%H%M%S' )}"

                # Сатууну кошуу - ТҮЗӨТҮЛДҮ (sale_date эмес, created_at колдонулбайт)
                cursor.execute ( """
                    INSERT INTO sales (invoice_number, user_id, total_amount, payment_amount, change_amount, payment_method, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (invoice_number, user_id, total_amount, payment_amount, change_amount, payment_method, notes) )

                sale_id = cursor.lastrowid

                # Сатуу элементтерин кошуу жана складды жаңыртуу
                for item in items:
                    cursor.execute ( """
                        INSERT INTO sale_items (sale_id, product_id, quantity, price, total)
                        VALUES (?, ?, ?, ?, ?)
                    """, (sale_id, item['product_id'], item['quantity'], item['price'], item['total']) )

                    # Складды азайтуу
                    cursor.execute ( "UPDATE products SET stock = stock - ? WHERE id = ?",
                                     (item['quantity'], item['product_id']) )

                return True, {
                    'sale_id': sale_id,
                    'invoice_number': invoice_number,
                    'total_amount': total_amount,
                    'change_amount': change_amount
                }
        except Exception as e:
            return False, str ( e )

    def get_sales(self, start_date: str = None, end_date: str = None) -> List[Sale]:
        """Сатууларды алуу"""
        with self.get_connection () as conn:
            cursor = conn.cursor ()
            query = """
                SELECT s.*, u.username, u.full_name as user_full_name
                FROM sales s
                JOIN users u ON s.user_id = u.id
                WHERE 1=1
            """
            params = []

            if start_date:
                query += " AND DATE(s.created_at) >= ?"
                params.append ( start_date )
            if end_date:
                query += " AND DATE(s.created_at) <= ?"
                params.append ( end_date )

            query += " ORDER BY s.created_at DESC"

            cursor.execute ( query, params )
            rows = cursor.fetchall ()

            sales = []
            for row in rows:
                data = dict ( row )
                # Сатуу элементтерин алуу
                cursor.execute ( """
                    SELECT si.*, p.name as product_name, p.unit_type
                    FROM sale_items si
                    JOIN products p ON si.product_id = p.id
                    WHERE si.sale_id = ?
                """, (data['id'],) )
                items_rows = cursor.fetchall ()
                items = []
                for item_row in items_rows:
                    item_data = dict ( item_row )
                    items.append ( SaleItem ( **item_data ) )

                sales.append ( Sale ( **data, items=items ) )

            return sales

    def get_sale_by_id(self, sale_id: int) -> Optional[Sale]:
        """ID боюнча сатуу алуу"""
        with self.get_connection () as conn:
            cursor = conn.cursor ()
            cursor.execute ( """
                SELECT s.*, u.username, u.full_name as user_full_name
                FROM sales s
                JOIN users u ON s.user_id = u.id
                WHERE s.id = ?
            """, (sale_id,) )
            row = cursor.fetchone ()

            if row:
                data = dict ( row )
                # Сатуу элементтерин алуу
                cursor.execute ( """
                    SELECT si.*, p.name as product_name, p.unit_type
                    FROM sale_items si
                    JOIN products p ON si.product_id = p.id
                    WHERE si.sale_id = ?
                """, (sale_id,) )
                items_rows = cursor.fetchall ()
                items = []
                for item_row in items_rows:
                    item_data = dict ( item_row )
                    items.append ( SaleItem ( **item_data ) )

                return Sale ( **data, items=items )
            return None

    # ==================== АНАЛИТИКА ====================

    def get_daily_sales(self, date: str = None) -> Dict:
        """Күндүк сатуу статистикасы"""
        if not date:
            date = datetime.now ().strftime ( '%Y-%m-%d' )

        with self.get_connection () as conn:
            cursor = conn.cursor ()

            # Жалпы сатуу - ТҮЗӨТҮЛДҮ (created_at колдонуу)
            cursor.execute ( """
                SELECT COUNT(*) as count, COALESCE(SUM(total_amount), 0) as total
                FROM sales
                WHERE DATE(created_at) = ?
            """, (date,) )
            sales_data = cursor.fetchone ()

            # Сатуулардын саны
            cursor.execute ( "SELECT COUNT(*) FROM sales WHERE DATE(created_at) = ?", (date,) )
            sales_count = cursor.fetchone ()[0]

            # Орточо чек
            avg_check = sales_data[1] / sales_count if sales_count > 0 else 0

            return {
                'date': date,
                'sales_count': sales_count,
                'total_amount': sales_data[1] if sales_data else 0,
                'avg_check': avg_check
            }

    def get_top_products(self, limit: int = 10, days: int = 30) -> List[Dict]:
        """Эң көп сатылган товарлар"""
        with self.get_connection () as conn:
            cursor = conn.cursor ()
            cursor.execute ( """
                SELECT p.id, p.name, SUM(si.quantity) as total_quantity, SUM(si.total) as total_revenue
                FROM sale_items si
                JOIN products p ON si.product_id = p.id
                JOIN sales s ON si.sale_id = s.id
                WHERE s.created_at >= DATE('now', ?)
                GROUP BY p.id, p.name
                ORDER BY total_quantity DESC
                LIMIT ?
            """, (f'-{days} days', limit) )
            rows = cursor.fetchall ()
            return [dict ( row ) for row in rows]

    def close(self):
        """Маалымат базасын жабуу"""
        pass