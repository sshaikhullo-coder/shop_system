# utils/receipt_printer.py
import os
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
import hashlib


class ReceiptPrinter:
    def __init__(self):
        self.receipt_dir = "receipts"
        os.makedirs ( self.receipt_dir, exist_ok=True )

    def print_receipt(self, sale_data, items, change=0, cashier_name="Кассир"):
        """
        Сатуу чектерин чыгаруу

        Args:
            sale_data (dict): Сатуу маалыматтары
            items (list): Сатылган товарлар
            change (float): Кайтарылган акча
            cashier_name (str): Кассирдин аты
        """
        try:
            filename = f"{self.receipt_dir}/receipt_{sale_data['sale_number']}.txt"

            with open ( filename, 'w', encoding='utf-8' ) as f:
                # Чектин башы
                f.write ( "=" * 40 + "\n" )
                f.write ( "         SHOP SYSTEM          \n" )
                f.write ( "      САТУУ КВИТАНЦИЯСЫ        \n" )
                f.write ( "=" * 40 + "\n\n" )

                f.write ( f"Чек №: {sale_data['sale_number']}\n" )
                f.write ( f"Дата: {sale_data['created_at'].strftime ( '%d.%m.%Y %H:%M' )}\n" )
                f.write ( f"Кассир: {cashier_name}\n\n" )

                # Товарлар
                f.write ( "-" * 40 + "\n" )
                f.write ( f"{'Товар':<20} {'Сан':>8} {'Баа':>6} {'Сумма':>8}\n" )
                f.write ( "-" * 40 + "\n" )

                for item in items:
                    name = item['product_name'][:18]
                    qty = f"{item['quantity']:.2f}"
                    price = f"{item['price']:.2f}"
                    total = f"{item['total']:.2f}"
                    f.write ( f"{name:<20} {qty:>8} {price:>6} {total:>8}\n" )

                f.write ( "-" * 40 + "\n" )
                f.write ( f"{'ЖАЛПЫ:':<28} {sale_data['total_amount']:>10.2f} сом\n" )
                f.write ( f"{'Төлөм:':<28} {sale_data['paid_amount']:>10.2f} сом\n" )
                if change > 0:
                    f.write ( f"{'Кайтарылды:':<28} {change:>10.2f} сом\n" )

                f.write ( "\n" + "=" * 40 + "\n" )
                f.write ( "      РАХМАТ! КАЙРА КЕЛИҢИЗ!      \n" )
                f.write ( "=" * 40 + "\n" )
                f.write ( f"Штрихкод: {hashlib.md5 ( sale_data['sale_number'].encode () ).hexdigest ()[:10]}\n" )

            # PDF версиясын да түзүү
            self._create_pdf_receipt ( sale_data, items, change, cashier_name )

            return filename
        except Exception as e:
            print ( f"Чек түзүүдө ката: {e}" )
            return None

    def _create_pdf_receipt(self, sale_data, items, change, cashier_name):
        """PDF форматында чек түзүү"""
        try:
            filename = f"{self.receipt_dir}/receipt_{sale_data['sale_number']}.pdf"
            doc = SimpleDocTemplate ( filename, pagesize=(80 * mm, 150 * mm) )
            styles = getSampleStyleSheet ()
            story = []

            title_style = ParagraphStyle (
                'ReceiptTitle',
                parent=styles['Normal'],
                fontSize=12,
                alignment=1,
                spaceAfter=6,
                fontName='Helvetica-Bold'
            )

            normal_style = ParagraphStyle (
                'Normal',
                parent=styles['Normal'],
                fontSize=9,
                spaceAfter=2
            )

            story.append ( Paragraph ( "SHOP SYSTEM", title_style ) )
            story.append ( Paragraph ( "САТУУ КВИТАНЦИЯСЫ", title_style ) )
            story.append ( Spacer ( 1, 5 ) )

            story.append ( Paragraph ( f"Чек №: {sale_data['sale_number']}", normal_style ) )
            story.append (
                Paragraph ( f"Дата: {sale_data['created_at'].strftime ( '%d.%m.%Y %H:%M' )}", normal_style ) )
            story.append ( Paragraph ( f"Кассир: {cashier_name}", normal_style ) )
            story.append ( Spacer ( 1, 8 ) )

            data = [['Товар', 'Сан', 'Сумма']]
            for item in items:
                data.append ( [
                    item['product_name'][:20],
                    f"{item['quantity']:.2f}",
                    f"{item['total']:.2f}"
                ] )

            table = Table ( data, colWidths=[40 * mm, 20 * mm, 25 * mm] )
            table.setStyle ( TableStyle ( [
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
            ] ) )
            story.append ( table )
            story.append ( Spacer ( 1, 8 ) )

            story.append ( Paragraph ( f"Жалпы: {sale_data['total_amount']:.2f} сом", normal_style ) )
            story.append ( Paragraph ( f"Төлөм: {sale_data['paid_amount']:.2f} сом", normal_style ) )
            if change > 0:
                story.append ( Paragraph ( f"Кайтарылды: {change:.2f} сом", normal_style ) )
            story.append ( Spacer ( 1, 5 ) )
            story.append ( Paragraph ( "Рахмат! Кайра келиңиз!", title_style ) )

            doc.build ( story )
        except Exception as e:
            print ( f"PDF чек түзүүдө ката: {e}" )