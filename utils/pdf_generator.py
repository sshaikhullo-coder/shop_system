"""
PDF отчетторду түзүү модулу
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import os
import matplotlib.pyplot as plt
import io
from datetime import datetime
import logging

logger = logging.getLogger ( __name__ )


class PDFGenerator:
    """PDF документтерди түзүү классы"""

    def __init__(self):
        self.reports_dir = "reports"
        os.makedirs ( self.reports_dir, exist_ok=True )
        logger.info ( "PDF генератор инициализацияланды" )

    def generate_report(self, data, filename):
        """
        Отчетту PDF форматында түзүү

        Args:
            data (dict): Отчет маалыматтары
            filename (str): Сакталуучу файлдын аты

        Returns:
            str: Түзүлгөн файлдын толук жолу
        """
        try:
            filename = os.path.join ( self.reports_dir, filename )
            doc = SimpleDocTemplate ( filename, pagesize=A4 )
            styles = getSampleStyleSheet ()
            story = []

            # Башкы аталыш
            title_style = ParagraphStyle (
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor ( '#2c3e50' ),
                alignment=1,
                spaceAfter=30
            )

            story.append ( Paragraph ( "Магазин Отчету", title_style ) )
            story.append ( Paragraph ( f"Дата: {datetime.now ().strftime ( '%d.%m.%Y %H:%M' )}", styles['Normal'] ) )
            story.append ( Spacer ( 1, 20 ) )

            # Жыйынтык таблицасы
            if 'summary' in data:
                summary_data = [
                    ['Көрсөткүч', 'Маани'],
                    ['Жалпы сатуулар', str ( data['summary'].get ( 'total_sales', 0 ) )],
                    ['Жалпы сумма', f"{data['summary'].get ( 'total_amount', 0 ):.2f} сом"],
                    ['Орточо чек', f"{data['summary'].get ( 'average_sale', 0 ):.2f} сом"],
                ]

                table = Table ( summary_data, colWidths=[3 * inch, 3 * inch] )
                table.setStyle ( TableStyle ( [
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor ( '#3498db' )),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige)
                ] ) )
                story.append ( table )
                story.append ( Spacer ( 1, 20 ) )

            # Товарлар таблицасы
            if 'products' in data and data['products']:
                story.append ( Paragraph ( "Товарлар боюнча сатуу", styles['Heading2'] ) )
                story.append ( Spacer ( 1, 10 ) )

                product_data = [['Товар', 'Саны', 'Сумма']]
                for product in data['products'][:20]:
                    product_data.append ( [
                        product.get ( 'name', '' )[:30],
                        f"{product.get ( 'quantity', 0 ):.2f}",
                        f"{product.get ( 'amount', 0 ):.2f} сом"
                    ] )

                product_table = Table ( product_data, colWidths=[3 * inch, 1.5 * inch, 2 * inch] )
                product_table.setStyle ( TableStyle ( [
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor ( '#2ecc71' )),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.black)
                ] ) )
                story.append ( product_table )

            doc.build ( story )
            logger.info ( f"PDF отчет түзүлдү: {filename}" )
            return filename

        except Exception as e:
            logger.error ( f"PDF түзүүдө ката: {e}" )
            return None

    def generate_sales_report(self, sales_data, filename):
        """
        Сатуу отчетун түзүү

        Args:
            sales_data (list): Сатуулар тизмеси
            filename (str): Файл аты

        Returns:
            str: Түзүлгөн файлдын жолу
        """
        try:
            filename = os.path.join ( self.reports_dir, filename )
            doc = SimpleDocTemplate ( filename, pagesize=landscape ( A4 ) )
            styles = getSampleStyleSheet ()
            story = []

            story.append ( Paragraph ( "Сатуу Отчету", styles['Heading1'] ) )
            story.append ( Spacer ( 1, 20 ) )

            # Сатуулар таблицасы
            data = [['Чек №', 'Дата', 'Кассир', 'Төлөм түрү', 'Сумма']]
            for sale in sales_data:
                data.append ( [
                    sale.get ( 'sale_number', '' ),
                    sale.get ( 'date', '' ),
                    sale.get ( 'cashier', '' ),
                    sale.get ( 'payment_type', '' ),
                    f"{sale.get ( 'amount', 0 ):.2f} сом"
                ] )

            table = Table ( data, colWidths=[1.5 * inch, 1.5 * inch, 1.5 * inch, 1.2 * inch, 1.2 * inch] )
            table.setStyle ( TableStyle ( [
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black)
            ] ) )
            story.append ( table )

            doc.build ( story )
            return filename

        except Exception as e:
            logger.error ( f"Сатуу отчетун түзүүдө ката: {e}" )
            return None