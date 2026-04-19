"""
Пайда эсептөө модулу - Professional Version
Киргизилген товарлардан түшкөн пайданы эсептөө үчүн
"""

from database.db_manager import DatabaseManager
from database.models import Sale, SaleItem, Product, ProfitLog
from datetime import datetime, timedelta
from sqlalchemy import func, and_, desc
import logging

logger = logging.getLogger ( __name__ )


class ProfitCalculator:
    """
    Пайда эсептөө классы

    Ар бир товардан түшкөн пайданы эсептейт:
    Пайда = (Сатуу баасы - Сатып алуу баасы) × Сатылган сан
    Мисал: 50 сомго алынган товар 70 сомго сатылса → пайда 20 сом
    """

    def __init__(self):
        self.db = DatabaseManager ()
        logger.info ( "ProfitCalculator инициализацияланды" )

    def get_session(self):
        """База сессиясын алуу"""
        return self.db.get_session ()

    # ==================== НЕГИЗГИ ПАЙДА ФУНКЦИЯЛАРЫ ====================

    def calculate_product_profit(self, product_id, quantity, selling_price):
        """
        Бир товардан түшкөн пайданы эсептөө

        Args:
            product_id (int): Товар ID
            quantity (float): Сатылган сан
            selling_price (float): Сатуу баасы

        Returns:
            dict: Пайда маалыматтары
        """
        session = self.get_session ()
        try:
            product = session.query ( Product ).filter_by ( id=product_id ).first ()
            if not product:
                logger.warning ( f"Товар табылган жок: ID={product_id}" )
                return None

            cost_price = product.cost_price
            profit_per_unit = selling_price - cost_price
            total_profit = profit_per_unit * quantity
            profit_percent = (profit_per_unit / cost_price * 100) if cost_price > 0 else 0

            return {
                'product_id': product.id,
                'product_name': product.name,
                'barcode': product.barcode,
                'cost_price': cost_price,
                'selling_price': selling_price,
                'quantity': quantity,
                'profit_per_unit': profit_per_unit,
                'total_profit': total_profit,
                'profit_percent': profit_percent,
                'category': product.category.name if product.category else None
            }
        finally:
            session.close ()

    def calculate_sale_profit(self, sale_id):
        """
        Бир сатуудан түшкөн жалпы пайданы эсептөө

        Args:
            sale_id (int): Сатуу ID

        Returns:
            dict: Сатуунун пайда маалыматтары
        """
        session = self.get_session ()
        try:
            sale = session.query ( Sale ).filter_by ( id=sale_id ).first ()
            if not sale:
                logger.warning ( f"Сатуу табылган жок: ID={sale_id}" )
                return None

            items = session.query ( SaleItem ).filter_by ( sale_id=sale_id ).all ()

            total_profit = 0
            profit_details = []

            for item in items:
                product = session.query ( Product ).filter_by ( id=item.product_id ).first ()
                if product:
                    profit_per_unit = item.price - product.cost_price
                    profit = profit_per_unit * item.quantity
                    total_profit += profit

                    profit_details.append ( {
                        'product_name': product.name,
                        'quantity': item.quantity,
                        'selling_price': item.price,
                        'cost_price': product.cost_price,
                        'profit': profit,
                        'profit_per_unit': profit_per_unit
                    } )

            return {
                'sale_id': sale.id,
                'sale_number': sale.sale_number,
                'created_at': sale.created_at,
                'total_amount': sale.total_amount,
                'total_profit': total_profit,
                'profit_percent': (total_profit / sale.total_amount * 100) if sale.total_amount > 0 else 0,
                'items': profit_details
            }
        finally:
            session.close ()

    # ==================== ЖАЛПЫ ПАЙДА СТАТИСТИКАСЫ ====================

    def get_total_profit(self, start_date=None, end_date=None):
        """
        Жалпы пайданы эсептөө (белгилүү мезгил үчүн)

        Args:
            start_date (datetime): Башталгыч дата
            end_date (datetime): Аяктоочу дата

        Returns:
            float: Жалпы пайда суммасы
        """
        session = self.get_session ()
        try:
            query = session.query (
                func.sum ( (Product.price - Product.cost_price) * SaleItem.quantity )
            ).join ( SaleItem, SaleItem.product_id == Product.id ) \
                .join ( Sale, Sale.id == SaleItem.sale_id )

            if start_date:
                query = query.filter ( Sale.created_at >= start_date )
            if end_date:
                query = query.filter ( Sale.created_at <= end_date )

            total = query.scalar () or 0
            logger.info ( f"Жалпы пайда: {total:.2f} сом" )
            return total
        finally:
            session.close ()

    def get_total_profit_by_payment_type(self, start_date=None, end_date=None):
        """
        Төлөм түрлөрү боюнча пайда

        Returns:
            dict: Накталай, карта, насыя боюнча пайда
        """
        session = self.get_session ()
        try:
            from database.models import PaymentType

            query = session.query (
                Sale.payment_type,
                func.sum ( (Product.price - Product.cost_price) * SaleItem.quantity ).label ( 'profit' )
            ).join ( SaleItem, SaleItem.sale_id == Sale.id ) \
                .join ( Product, Product.id == SaleItem.product_id ) \
                .join ( Sale, Sale.id == SaleItem.sale_id )

            if start_date:
                query = query.filter ( Sale.created_at >= start_date )
            if end_date:
                query = query.filter ( Sale.created_at <= end_date )

            results = query.group_by ( Sale.payment_type ).all ()

            profit_by_type = {
                'cash': 0,
                'card': 0,
                'credit': 0
            }

            for r in results:
                if r[0].value == 'cash':
                    profit_by_type['cash'] = r[1] or 0
                elif r[0].value == 'card':
                    profit_by_type['card'] = r[1] or 0
                elif r[0].value == 'credit':
                    profit_by_type['credit'] = r[1] or 0

            return profit_by_type
        finally:
            session.close ()

    # ==================== ТОВАРЛАР БОЮНЧА ПАЙДА ====================

    def get_profit_by_product(self, start_date=None, end_date=None, limit=50):
        """
        Товарлар боюнча пайда (эң көп пайда алып келген товарлар)

        Args:
            start_date (datetime): Башталгыч дата
            end_date (datetime): Аяктоочу дата
            limit (int): Чектөө саны

        Returns:
            list: Товарлардын пайда маалыматтары
        """
        session = self.get_session ()
        try:
            query = session.query (
                Product.id,
                Product.name,
                Product.barcode,
                func.sum ( SaleItem.quantity ).label ( 'total_quantity' ),
                func.sum ( (Product.price - Product.cost_price) * SaleItem.quantity ).label ( 'total_profit' ),
                func.avg ( (Product.price - Product.cost_price) / Product.cost_price * 100 ).label ( 'avg_percent' ),
                Product.cost_price,
                Product.price
            ).join ( SaleItem, SaleItem.product_id == Product.id ) \
                .join ( Sale, Sale.id == SaleItem.sale_id ) \
                .group_by ( Product.id ) \
                .order_by ( desc ( 'total_profit' ) )

            if start_date:
                query = query.filter ( Sale.created_at >= start_date )
            if end_date:
                query = query.filter ( Sale.created_at <= end_date )

            results = query.limit ( limit ).all ()

            profit_data = []
            for r in results:
                profit_data.append ( {
                    'product_id': r[0],
                    'product_name': r[1],
                    'barcode': r[2] or '-',
                    'quantity_sold': r[3] or 0,
                    'total_profit': r[4] or 0,
                    'profit_percent': r[5] or 0,
                    'cost_price': r[6] or 0,
                    'selling_price': r[7] or 0,
                    'profit_per_unit': (r[7] or 0) - (r[6] or 0)
                } )

            return profit_data
        finally:
            session.close ()

    def get_low_profit_products(self, threshold=100, start_date=None, end_date=None):
        """
        Аз пайда алып келген товарлар (threshold чектен төмөн)

        Args:
            threshold (float): Пайда чеги
            start_date (datetime): Башталгыч дата
            end_date (datetime): Аяктоочу дата

        Returns:
            list: Аз пайдалуу товарлар
        """
        session = self.get_session ()
        try:
            query = session.query (
                Product.id,
                Product.name,
                func.sum ( SaleItem.quantity ).label ( 'total_quantity' ),
                func.sum ( (Product.price - Product.cost_price) * SaleItem.quantity ).label ( 'total_profit' )
            ).join ( SaleItem, SaleItem.product_id == Product.id ) \
                .join ( Sale, Sale.id == SaleItem.sale_id ) \
                .group_by ( Product.id ) \
                .having ( func.sum ( (Product.price - Product.cost_price) * SaleItem.quantity ) < threshold )

            if start_date:
                query = query.filter ( Sale.created_at >= start_date )
            if end_date:
                query = query.filter ( Sale.created_at <= end_date )

            results = query.all ()

            return [{
                'product_id': r[0],
                'product_name': r[1],
                'quantity_sold': r[2] or 0,
                'total_profit': r[3] or 0
            } for r in results]
        finally:
            session.close ()

    # ==================== УБАКЫТ БОЮНЧА ПАЙДА ====================

    def get_daily_profit(self, days=30):
        """
        Күндүк пайда (акыркы days күн үчүн)

        Args:
            days (int): Күндөрдүн саны

        Returns:
            list: Күндөр боюнча пайда
        """
        session = self.get_session ()
        try:
            end_date = datetime.now ()
            start_date = end_date - timedelta ( days=days )

            results = session.query (
                func.date ( Sale.created_at ).label ( 'date' ),
                func.sum ( (Product.price - Product.cost_price) * SaleItem.quantity ).label ( 'total_profit' ),
                func.count ( Sale.id ).label ( 'sales_count' )
            ).join ( SaleItem, SaleItem.product_id == Product.id ) \
                .join ( Sale, Sale.id == SaleItem.sale_id ) \
                .filter ( Sale.created_at >= start_date, Sale.created_at <= end_date ) \
                .group_by ( func.date ( Sale.created_at ) ) \
                .order_by ( func.date ( Sale.created_at ) ).all ()

            daily_data = []
            for r in results:
                daily_data.append ( {
                    'date': r[0],
                    'profit': r[1] or 0,
                    'sales_count': r[2] or 0
                } )

            return daily_data
        finally:
            session.close ()

    def get_weekly_profit(self, weeks=12):
        """
        Апталык пайда

        Args:
            weeks (int): Апталардын саны

        Returns:
            list: Апталар боюнча пайда
        """
        session = self.get_session ()
        try:
            end_date = datetime.now ()
            start_date = end_date - timedelta ( weeks=weeks )

            results = session.query (
                func.strftime ( '%Y-%W', Sale.created_at ).label ( 'week' ),
                func.sum ( (Product.price - Product.cost_price) * SaleItem.quantity ).label ( 'total_profit' ),
                func.count ( Sale.id ).label ( 'sales_count' )
            ).join ( SaleItem, SaleItem.product_id == Product.id ) \
                .join ( Sale, Sale.id == SaleItem.sale_id ) \
                .filter ( Sale.created_at >= start_date, Sale.created_at <= end_date ) \
                .group_by ( 'week' ) \
                .order_by ( 'week' ).all ()

            weekly_data = []
            for r in results:
                weekly_data.append ( {
                    'week': r[0],
                    'profit': r[1] or 0,
                    'sales_count': r[2] or 0
                } )

            return weekly_data
        finally:
            session.close ()

    def get_monthly_profit(self, months=12):
        """
        Айлык пайда

        Args:
            months (int): Айлардын саны

        Returns:
            list: Айлар боюнча пайда
        """
        session = self.get_session ()
        try:
            end_date = datetime.now ()
            start_date = end_date - timedelta ( days=months * 30 )

            results = session.query (
                func.strftime ( '%Y-%m', Sale.created_at ).label ( 'month' ),
                func.sum ( (Product.price - Product.cost_price) * SaleItem.quantity ).label ( 'total_profit' ),
                func.count ( Sale.id ).label ( 'sales_count' )
            ).join ( SaleItem, SaleItem.product_id == Product.id ) \
                .join ( Sale, Sale.id == SaleItem.sale_id ) \
                .filter ( Sale.created_at >= start_date, Sale.created_at <= end_date ) \
                .group_by ( 'month' ) \
                .order_by ( 'month' ).all ()

            monthly_data = []
            for r in results:
                monthly_data.append ( {
                    'month': r[0],
                    'profit': r[1] or 0,
                    'sales_count': r[2] or 0
                } )

            return monthly_data
        finally:
            session.close ()

    # ==================== КАТЕГОРИЯ БОЮНЧА ПАЙДА ====================

    def get_profit_by_category(self, start_date=None, end_date=None):
        """
        Категориялар боюнча пайда

        Returns:
            list: Категориялар боюнча пайда маалыматтары
        """
        session = self.get_session ()
        try:
            results = session.query (
                Product.category_id,
                func.sum ( SaleItem.quantity ).label ( 'total_quantity' ),
                func.sum ( (Product.price - Product.cost_price) * SaleItem.quantity ).label ( 'total_profit' )
            ).join ( SaleItem, SaleItem.product_id == Product.id ) \
                .join ( Sale, Sale.id == SaleItem.sale_id ) \
                .group_by ( Product.category_id )

            if start_date:
                results = results.filter ( Sale.created_at >= start_date )
            if end_date:
                results = results.filter ( Sale.created_at <= end_date )

            category_profit = []
            for r in results:
                # Категория атын алуу
                from database.models import Category
                category = session.query ( Category ).filter_by ( id=r[0] ).first ()
                category_name = category.name if category else "Категориясыз"

                category_profit.append ( {
                    'category_id': r[0],
                    'category_name': category_name,
                    'quantity_sold': r[1] or 0,
                    'total_profit': r[2] or 0
                } )

            return sorted ( category_profit, key=lambda x: x['total_profit'], reverse=True )
        finally:
            session.close ()

    # ==================== КОЛДОНУУЧУ БОЮНЧА ПАЙДА ====================

    def get_profit_by_user(self, start_date=None, end_date=None):
        """
        Колдонуучулар (кассирлер) боюнча пайда

        Returns:
            list: Колдонуучулар боюнча пайда маалыматтары
        """
        session = self.get_session ()
        try:
            from database.models import User

            results = session.query (
                User.id,
                User.username,
                User.full_name,
                func.sum ( (Product.price - Product.cost_price) * SaleItem.quantity ).label ( 'total_profit' ),
                func.count ( Sale.id ).label ( 'sales_count' )
            ).join ( Sale, Sale.user_id == User.id ) \
                .join ( SaleItem, SaleItem.sale_id == Sale.id ) \
                .join ( Product, Product.id == SaleItem.product_id ) \
                .group_by ( User.id )

            if start_date:
                results = results.filter ( Sale.created_at >= start_date )
            if end_date:
                results = results.filter ( Sale.created_at <= end_date )

            user_profit = []
            for r in results:
                user_profit.append ( {
                    'user_id': r[0],
                    'username': r[1],
                    'full_name': r[2],
                    'total_profit': r[3] or 0,
                    'sales_count': r[4] or 0,
                    'avg_profit_per_sale': (r[3] / r[4]) if r[4] and r[4] > 0 else 0
                } )

            return sorted ( user_profit, key=lambda x: x['total_profit'], reverse=True )
        finally:
            session.close ()

    # ==================== ПАЙДА ЛОГДОРУ ====================

    def save_profit_log(self, sale_id, product_id, quantity, selling_price):
        """
        Пайда логун сактоо

        Args:
            sale_id (int): Сатуу ID
            product_id (int): Товар ID
            quantity (float): Сатылган сан
            selling_price (float): Сатуу баасы

        Returns:
            bool: Ийгиликтүү болсо True
        """
        session = self.get_session ()
        try:
            product = session.query ( Product ).filter_by ( id=product_id ).first ()
            if not product:
                logger.warning ( f"Profit log: товар табылган жок ID={product_id}" )
                return False

            profit = (selling_price - product.cost_price) * quantity
            profit_percent = ((
                                          selling_price - product.cost_price) / product.cost_price * 100) if product.cost_price > 0 else 0

            profit_log = ProfitLog (
                product_id=product_id,
                product_name=product.name,
                sale_id=sale_id,
                quantity=quantity,
                selling_price=selling_price,
                cost_price=product.cost_price,
                profit=profit,
                profit_percent=profit_percent
            )
            session.add ( profit_log )
            session.commit ()

            logger.info ( f"Profit log сакталды: {product.name} - пайда: {profit:.2f} сом" )
            return True
        except Exception as e:
            session.rollback ()
            logger.error ( f"Profit log сактоодо ката: {e}" )
            return False
        finally:
            session.close ()

    def get_profit_logs(self, start_date=None, end_date=None, limit=100):
        """
        Пайда логдорун алуу

        Args:
            start_date (datetime): Башталгыч дата
            end_date (datetime): Аяктоочу дата
            limit (int): Чектөө саны

        Returns:
            list: Пайда логдору
        """
        session = self.get_session ()
        try:
            query = session.query ( ProfitLog ).order_by ( ProfitLog.created_at.desc () )

            if start_date:
                query = query.filter ( ProfitLog.created_at >= start_date )
            if end_date:
                query = query.filter ( ProfitLog.created_at <= end_date )

            logs = query.limit ( limit ).all ()

            return [{
                'id': l.id,
                'product_name': l.product_name,
                'quantity': l.quantity,
                'selling_price': l.selling_price,
                'cost_price': l.cost_price,
                'profit': l.profit,
                'profit_percent': l.profit_percent,
                'created_at': l.created_at,
                'sale_id': l.sale_id
            } for l in logs]
        finally:
            session.close ()

    # ==================== АНАЛИТИКА ЖАНА СТАТИСТИКА ====================

    def get_profit_summary(self, start_date=None, end_date=None):
        """
        Пайда жыйынтык отчету

        Returns:
            dict: Толук пайда статистикасы
        """
        session = self.get_session ()
        try:
            total_profit = self.get_total_profit ( start_date, end_date )
            profit_by_product = self.get_profit_by_product ( start_date, end_date, 10 )
            profit_by_category = self.get_profit_by_category ( start_date, end_date )
            profit_by_user = self.get_profit_by_user ( start_date, end_date )
            daily_profit = self.get_daily_profit ( 30 )

            # Эң көп пайда алып келген товар
            top_product = profit_by_product[0] if profit_by_product else None

            # Эң көп пайда алып келген категория
            top_category = profit_by_category[0] if profit_by_category else None

            # Эң көп пайда алып келген кассир
            top_user = profit_by_user[0] if profit_by_user else None

            return {
                'total_profit': total_profit,
                'top_product': top_product,
                'top_category': top_category,
                'top_user': top_user,
                'profit_by_product': profit_by_product[:5],
                'profit_by_category': profit_by_category[:5],
                'profit_by_user': profit_by_user[:5],
                'daily_profit': daily_profit[-7:],  # Соңку 7 күн
                'total_sales': len ( session.query ( Sale ).filter ( Sale.created_at >= start_date,
                                                                     Sale.created_at <= end_date ).all () ) if start_date and end_date else 0
            }
        finally:
            session.close ()

    def get_profit_chart_data(self, period='daily', days=30):
        """
        График үчүн пайда маалыматтары

        Args:
            period (str): 'daily', 'weekly', 'monthly'
            days (int): Күндөрдүн саны

        Returns:
            dict: График үчүн маалыматтар
        """
        if period == 'daily':
            data = self.get_daily_profit ( days )
            return {
                'labels': [d['date'] for d in data],
                'values': [d['profit'] for d in data],
                'sales_counts': [d['sales_count'] for d in data]
            }
        elif period == 'weekly':
            data = self.get_weekly_profit ( 12 )
            return {
                'labels': [d['week'] for d in data],
                'values': [d['profit'] for d in data],
                'sales_counts': [d['sales_count'] for d in data]
            }
        elif period == 'monthly':
            data = self.get_monthly_profit ( 12 )
            return {
                'labels': [d['month'] for d in data],
                'values': [d['profit'] for d in data],
                'sales_counts': [d['sales_count'] for d in data]
            }
        else:
            return {'labels': [], 'values': [], 'sales_counts': []}

    # ==================== ЭСКЕРТҮҮ ФУНКЦИЯЛАРЫ ====================

    def check_low_margin_products(self, margin_threshold=10):
        """
        Пайда пайызы төмөн товарларды текшерүү

        Args:
            margin_threshold (float): Пайда пайызынын чеги (%)

        Returns:
            list: Пайдасы төмөн товарлар
        """
        session = self.get_session ()
        try:
            products = session.query ( Product ).filter ( Product.is_active == True ).all ()

            low_margin = []
            for p in products:
                if p.cost_price > 0:
                    margin = (p.price - p.cost_price) / p.cost_price * 100
                    if margin < margin_threshold:
                        low_margin.append ( {
                            'product_id': p.id,
                            'product_name': p.name,
                            'cost_price': p.cost_price,
                            'selling_price': p.price,
                            'margin': margin,
                            'stock': p.stock
                        } )

            return sorted ( low_margin, key=lambda x: x['margin'] )
        finally:
            session.close ()

    # ==================== ПОЛЕЗДУУ ФУНКЦИЯЛАР ====================

    def format_profit(self, amount):
        """
        Пайданы форматтоо (кооз көрүнүш үчүн)

        Args:
            amount (float): Пайда суммасы

        Returns:
            str: Форматталган текст
        """
        if amount >= 1000000:
            return f"{amount / 1000000:.1f} млн сом"
        elif amount >= 1000:
            return f"{amount / 1000:.1f} миң сом"
        else:
            return f"{amount:.0f} сом"

    def get_profit_color(self, amount):
        """
        Пайданын көлөмүнө жараша түс кайтаруу

        Args:
            amount (float): Пайда суммасы

        Returns:
            tuple: RGB түсү
        """
        if amount <= 0:
            return (0.8, 0.2, 0.2, 1)  # Кызыл - пайда жок
        elif amount < 1000:
            return (0.95, 0.6, 0.2, 1)  # Сары - аз пайда
        elif amount < 10000:
            return (0.2, 0.7, 0.2, 1)  # Жашыл - орточо пайда
        else:
            return (0.1, 0.5, 0.8, 1)  # Көк - көп пайда