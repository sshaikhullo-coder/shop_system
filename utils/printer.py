import os
from datetime import datetime


class Printer:
    def __init__(self):
        self.receipt_dir = "receipts"
        os.makedirs ( self.receipt_dir, exist_ok=True )

    def print_receipt(self, sale, items, change):
        try:
            filename = f"{self.receipt_dir}/receipt_{sale.sale_number}.txt"
            with open ( filename, 'w', encoding='utf-8' ) as f:
                f.write ( "=" * 40 + "\n" )
                f.write ( "          МАГАЗИН          \n" )
                f.write ( "       САТУУ КВИТАНЦИЯСЫ     \n" )
                f.write ( "=" * 40 + "\n\n" )
                f.write ( f"Чек №: {sale.sale_number}\n" )
                f.write ( f"Дата: {sale.created_at.strftime ( '%d.%m.%Y %H:%M' )}\n" )
                f.write ( f"Кассир: {sale.user.full_name}\n\n" )
                f.write ( "-" * 40 + "\n" )
                f.write ( f"{'Товар':<20} {'Сан':>8} {'Сумма':>10}\n" )
                f.write ( "-" * 40 + "\n" )

                for item in items:
                    name = item['product'].name[:18]
                    qty = f"{item['quantity']:.2f}"
                    total = f"{item['total']:.2f}"
                    f.write ( f"{name:<20} {qty:>8} {total:>10}\n" )

                f.write ( "-" * 40 + "\n" )
                f.write ( f"{'Жалпы:':<28} {sale.total_amount:>10.2f}\n" )
                f.write ( f"{'Төлөм:':<28} {sale.paid_amount:>10.2f}\n" )
                if change > 0:
                    f.write ( f"{'Кайтарылды:':<28} {change:>10.2f}\n" )
                f.write ( "\n" + "=" * 40 + "\n" )
                f.write ( "      РАХМАТ! КАЙРА КЕЛИҢИЗ!      \n" )
                f.write ( "=" * 40 + "\n" )

            return filename
        except Exception as e:
            print ( f"Error printing receipt: {e}" )
            return None