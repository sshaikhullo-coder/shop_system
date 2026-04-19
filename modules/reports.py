from database.db_manager import DatabaseManager
from database.models import Sale, SaleItem, Product, PaymentType, User
from datetime import datetime, timedelta
from sqlalchemy import func
import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch


class ReportManager:
    def __init__(self):
        self.db = DatabaseManager ()

    def get_session(self):
        return self.db.get_session ()

    def get_sales_summary(self, start_date, end_date):
        """Жалпы сатуу жыйынтыгы"""
        session = self.get_session ()
        try:
            sales = session.query ( Sale ).filter (
                Sale.created_at >= start_date,
                Sale.created_at <= end_date
            ).all ()

            summary = {
                'total_sales': len ( sales ),
                'total_amount': sum ( s.total_amount for s in sales ),
                'cash_amount': sum ( s.total_amount for s in sales if s.payment_type == PaymentType.CASH ),
                'card_amount': sum ( s.total_amount for s in sales if s.payment_type == PaymentType.CARD ),
                'credit_amount': sum ( s.total_amount for s in sales if s.payment_type == PaymentType.CREDIT ),
                'average_sale': sum ( s.total_amount for s in sales ) / len ( sales ) if sales else 0
            }
            return summary
        finally:
            session.close ()

    def get_sales_by_user(self, start_date, end_date):
        """Ар бир колдонуучунун сатуулары"""
        session = self.get_session ()
        try:
            results = session.query (
                User.id,
                User.username,
                User.full_name,
                User.role,
                func.count ( Sale.id ).label ( 'sale_count' ),
                func.sum ( Sale.total_amount ).label ( 'total_amount' ),
                func.sum ( SaleItem.quantity ).label ( 'total_items' )
            ).join ( Sale, Sale.user_id == User.id ) \
                .join ( SaleItem, SaleItem.sale_id == Sale.id ) \
                .filter ( Sale.created_at >= start_date, Sale.created_at <= end_date ) \
                .group_by ( User.id ) \
                .order_by ( func.sum ( Sale.total_amount ).desc () ).all ()
            return results
        finally:
            session.close ()

    def get_user_daily_sales(self, user_id, date):
        """Белгилүү колдонуучунун күндүк сатуулары"""
        session = self.get_session ()
        try:
            start = datetime.combine ( date, datetime.min.time () )
            end = datetime.combine ( date, datetime.max.time () )

            sales = session.query ( Sale ).filter (
                Sale.user_id == user_id,
                Sale.created_at >= start,
                Sale.created_at <= end
            ).all ()

            total_amount = sum ( s.total_amount for s in sales )
            total_items = sum ( len ( s.items ) for s in sales )

            return {
                'sales_count': len ( sales ),
                'total_amount': total_amount,
                'total_items': total_items,
                'sales': sales
            }
        finally:
            session.close ()

    def get_user_weekly_report(self, user_id, start_date, end_date):
        """Колдонуучунун апталык отчету"""
        session = self.get_session ()
        try:
            # Күндүк бөлүнүш
            daily = session.query (
                func.date ( Sale.created_at ).label ( 'date' ),
                func.count ( Sale.id ).label ( 'count' ),
                func.sum ( Sale.total_amount ).label ( 'total' ),
                func.sum ( SaleItem.quantity ).label ( 'items' )
            ).join ( SaleItem, SaleItem.sale_id == Sale.id ) \
                .filter (
                Sale.user_id == user_id,
                Sale.created_at >= start_date,
                Sale.created_at <= end_date
            ).group_by ( func.date ( Sale.created_at ) ).all ()

            # Сааттык бөлүнүш
            hourly = session.query (
                func.strftime ( '%H', Sale.created_at ).label ( 'hour' ),
                func.count ( Sale.id ).label ( 'count' ),
                func.sum ( Sale.total_amount ).label ( 'total' )
            ).filter (
                Sale.user_id == user_id,
                Sale.created_at >= start_date,
                Sale.created_at <= end_date
            ).group_by ( 'hour' ).order_by ( 'hour' ).all ()

            return {
                'daily': daily,
                'hourly': hourly,
                'total_sales': sum ( d[1] for d in daily ),
                'total_amount': sum ( d[2] for d in daily ),
                'total_items': sum ( d[3] for d in daily )
            }
        finally:
            session.close ()

    def get_all_users_report(self, start_date, end_date):
        """Бардык колдонуучулардын салыштырма отчету"""
        session = self.get_session ()
        try:
            results = session.query (
                User.id,
                User.username,
                User.full_name,
                User.role,
                func.count ( Sale.id ).label ( 'sale_count' ),
                func.sum ( Sale.total_amount ).label ( 'total_amount' ),
                func.sum ( SaleItem.quantity ).label ( 'total_items' )
            ).join ( Sale, Sale.user_id == User.id, isouter=True ) \
                .join ( SaleItem, SaleItem.sale_id == Sale.id, isouter=True ) \
                .filter (
                Sale.created_at >= start_date,
                Sale.created_at <= end_date
            ).group_by ( User.id ).all ()

            # Жалпы статистика
            total = session.query (
                func.count ( Sale.id ).label ( 'total_sales' ),
                func.sum ( Sale.total_amount ).label ( 'total_amount' ),
                func.sum ( SaleItem.quantity ).label ( 'total_items' )
            ).filter (
                Sale.created_at >= start_date,
                Sale.created_at <= end_date
            ).first ()

            return {
                'users': results,
                'total': {
                    'sales': total[0] or 0,
                    'amount': total[1] or 0,
                    'items': total[2] or 0
                }
            }
        finally:
            session.close ()

    def generate_pdf_report(self, start_date, end_date, filename):
        """PDF отчет түзүү"""
        try:
            os.makedirs ( "reports", exist_ok=True )
            filename = os.path.join ( "reports", filename )

            doc = SimpleDocTemplate ( filename, pagesize=A4 )
            styles = getSampleStyleSheet ()
            story = []

            title_style = ParagraphStyle (
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=20,
                alignment=1,
                spaceAfter=30
            )

            story.append ( Paragraph ( "МАГАЗИН САТУУ ОТЧЕТУ", title_style ) )
            story.append (
                Paragraph ( f"Дата: {start_date.strftime ( '%d.%m.%Y' )} - {end_date.strftime ( '%d.%m.%Y' )}",
                            styles['Normal'] ) )
            story.append ( Spacer ( 1, 20 ) )

            summary = self.get_sales_summary ( start_date, end_date )

            summary_data = [
                ['Көрсөткүч', 'Маани'],
                ['Жалпы сатуулар', f"{summary['total_sales']} даана"],
                ['Жалпы сумма', f"{summary['total_amount']:,.2f} сом"],
                ['Орточо чек', f"{summary['average_sale']:,.2f} сом"],
                ['Накталай', f"{summary['cash_amount']:,.2f} сом"],
                ['Карта', f"{summary['card_amount']:,.2f} сом"],
                ['Насыя', f"{summary['credit_amount']:,.2f} сом"]
            ]

            table = Table ( summary_data, colWidths=[3 * inch, 3 * inch] )
            table.setStyle ( TableStyle ( [
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ] ) )
            story.append ( table )

            doc.build ( story )
            return filename
        except Exception as e:
            print ( f"PDF error: {e}" )
            return None

    def generate_excel_report(self, start_date, end_date, filename):
        """Excel отчет түзүү - Pandas жок болсо иштебейт"""
        print ( "Excel отчету: Pandas модулу жок. 'pip install pandas' командасын иштетиңиз." )
        return None

    def generate_user_pdf_report(self, user_id, start_date, end_date, filename):
        """Колдонуучунун жеке PDF отчету"""
        try:
            os.makedirs ( "reports", exist_ok=True )
            filename = os.path.join ( "reports", filename )

            session = self.get_session ()
            user = session.query ( User ).filter_by ( id=user_id ).first ()

            doc = SimpleDocTemplate ( filename, pagesize=A4 )
            styles = getSampleStyleSheet ()
            story = []

            title_style = ParagraphStyle (
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=20,
                alignment=1,
                spaceAfter=30
            )

            story.append ( Paragraph ( f"Кассир Отчету: {user.full_name}", title_style ) )
            story.append (
                Paragraph ( f"Дата: {start_date.strftime ( '%d.%m.%Y' )} - {end_date.strftime ( '%d.%m.%Y' )}",
                            styles['Normal'] ) )
            story.append ( Spacer ( 1, 20 ) )

            report_data = self.get_user_weekly_report ( user_id, start_date, end_date )

            summary_data = [
                ['Көрсөткүч', 'Маани'],
                ['Жалпы сатуулар', f"{report_data['total_sales']} даана"],
                ['Жалпы сумма', f"{report_data['total_amount']:.2f} сом"],
                ['Сатылган товарлар', f"{report_data['total_items']} даана"],
                ['Орточо чек', f"{report_data['total_amount'] / report_data['total_sales']:.2f} сом" if report_data[
                                                                                                            'total_sales'] > 0 else "0 сом"]
            ]

            table = Table ( summary_data, colWidths=[3 * inch, 2 * inch] )
            table.setStyle ( TableStyle ( [
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ] ) )
            story.append ( table )
            story.append ( Spacer ( 1, 20 ) )

            if report_data['daily']:
                story.append ( Paragraph ( "Күндүк бөлүнүш", styles['Heading2'] ) )
                daily_data = [['Дата', 'Сатуулар', 'Сумма', 'Товарлар']]
                for d in report_data['daily']:
                    daily_data.append ( [d[0], str ( d[1] ), f"{d[2]:.2f}", str ( d[3] )] )

                daily_table = Table ( daily_data, colWidths=[1.5 * inch, 1.2 * inch, 1.5 * inch, 1.2 * inch] )
                daily_table.setStyle ( TableStyle ( [
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor ( '#3498db' )),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.black)
                ] ) )
                story.append ( daily_table )

            doc.build ( story )
            session.close ()
            return filename
        except Exception as e:
            print ( f"PDF error: {e}" )
            return None