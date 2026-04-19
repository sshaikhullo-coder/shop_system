"""
Билдирүүлөрдү жөнөтүү модулу (Telegram, Email)
"""

import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from datetime import datetime

logger = logging.getLogger ( __name__ )


class NotificationManager:
    """Билдирүүлөрдү башкаруу классы"""

    def __init__(self):
        self.smtp_config = {
            'server': 'smtp.gmail.com',
            'port': 587,
            'email': '',
            'password': ''
        }

        self.telegram_config = {
            'bot_token': '',
            'chat_id': ''
        }

        self.enabled = False
        logger.info ( "Билдирүү менеджери инициализацияланды" )

    def configure_telegram(self, bot_token, chat_id):
        """Telegram ботун конфигурациялоо"""
        self.telegram_config['bot_token'] = bot_token
        self.telegram_config['chat_id'] = chat_id
        self.enabled = True
        logger.info ( "Telegram конфигурацияланды" )

    def configure_email(self, email, password, server='smtp.gmail.com', port=587):
        """Email конфигурациялоо"""
        self.smtp_config['email'] = email
        self.smtp_config['password'] = password
        self.smtp_config['server'] = server
        self.smtp_config['port'] = port
        self.enabled = True
        logger.info ( "Email конфигурацияланды" )

    def send_telegram(self, message):
        """
        Telegram аркылуу билдирүү жөнөтүү

        Args:
            message (str): Жөнөтүлүүчү билдирүү

        Returns:
            tuple: (success, message)
        """
        try:
            if not self.telegram_config['bot_token'] or not self.telegram_config['chat_id']:
                return False, "Telegram конфигурациясы жок"

            url = f"https://api.telegram.org/bot{self.telegram_config['bot_token']}/sendMessage"
            data = {
                'chat_id': self.telegram_config['chat_id'],
                'text': message,
                'parse_mode': 'HTML'
            }

            response = requests.post ( url, data=data, timeout=10 )
            if response.status_code == 200:
                logger.info ( "Telegram билдирүү жөнөтүлдү" )
                return True, "Telegram билдирүү жөнөтүлдү"
            else:
                logger.error ( f"Telegram катасы: {response.text}" )
                return False, f"Ката: {response.text}"

        except Exception as e:
            logger.error ( f"Telegram билдирүү жөнөтүүдө ката: {e}" )
            return False, str ( e )

    def send_email(self, to_email, subject, body):
        """
        Email аркылуу билдирүү жөнөтүү

        Args:
            to_email (str): Алуучунун email дареги
            subject (str): Билдирүүнүн темасы
            body (str): Билдирүүнүн тексти

        Returns:
            tuple: (success, message)
        """
        try:
            if not self.smtp_config['email'] or not self.smtp_config['password']:
                return False, "Email конфигурациясы жок"

            msg = MIMEMultipart ()
            msg['From'] = self.smtp_config['email']
            msg['To'] = to_email
            msg['Subject'] = subject

            msg.attach ( MIMEText ( body, 'plain', 'utf-8' ) )

            server = smtplib.SMTP ( self.smtp_config['server'], self.smtp_config['port'] )
            server.starttls ()
            server.login ( self.smtp_config['email'], self.smtp_config['password'] )
            server.send_message ( msg )
            server.quit ()

            logger.info ( f"Email жөнөтүлдү: {to_email}" )
            return True, "Email жөнөтүлдү"

        except Exception as e:
            logger.error ( f"Email жөнөтүүдө ката: {e}" )
            return False, str ( e )

    def send_low_stock_alert(self, products):
        """
        Жетишсиз товарлар жөнүндө билдирүү жөнөтүү

        Args:
            products (list): Жетишсиз товарлардын тизмеси
        """
        if not products:
            return

        message = "⚠️ <b>ЖЕТИШСИЗ ТОВАРЛАР!</b>\n\n"
        for product in products[:10]:  # 10 товарга чейин
            message += f"📦 {product.name}\n"
            message += f"   Складда: {product.stock} {product.unit_type.value}\n"
            message += f"   Минималдуу: {product.min_stock}\n\n"

        if len ( products ) > 10:
            message += f"\n... жана дагы {len ( products ) - 10} товар"

        self.send_telegram ( message )

        # Emailге да жөнөтүү (конфигурацияланса)
        if self.smtp_config['email']:
            self.send_email (
                self.smtp_config['email'],
                "Жетишсиз товарлар эскертүүсү",
                message.replace ( '<b>', '' ).replace ( '</b>', '' )
            )

    def send_daily_report(self, sales_summary):
        """
        Күндүк отчетту жөнөтүү

        Args:
            sales_summary (dict): Сатуу жыйынтыктары
        """
        message = f"📊 <b>Күндүк Отчет</b>\n\n"
        message += f"📅 Дата: {datetime.now ().strftime ( '%d.%m.%Y' )}\n"
        message += f"💰 Жалпы сатуу: {sales_summary.get ( 'total_sales', 0 )} даана\n"
        message += f"💵 Жалпы сумма: {sales_summary.get ( 'total_amount', 0 ):.2f} сом\n"
        message += f"💳 Орточо чек: {sales_summary.get ( 'average_sale', 0 ):.2f} сом\n\n"

        message += f"💵 Накталай: {sales_summary.get ( 'cash_amount', 0 ):.2f} сом\n"
        message += f"💳 Карта: {sales_summary.get ( 'card_amount', 0 ):.2f} сом\n"
        message += f"📝 Насыя: {sales_summary.get ( 'credit_amount', 0 ):.2f} сом\n"

        self.send_telegram ( message )

    def send_backup_notification(self, backup_file, status='success'):
        """
        Резервдик көчүрмө жөнүндө билдирүү жөнөтүү

        Args:
            backup_file (str): Резервдик көчүрмө файлынын жолу
            status (str): Статус ('success' же 'failed')
        """
        if status == 'success':
            emoji = "✅"
            title = "Резервдик көчүрмө түзүлдү"
        else:
            emoji = "❌"
            title = "Резервдик көчүрмө түзүүдө ката"

        message = f"{emoji} <b>{title}</b>\n\n"
        message += f"📁 Файл: {backup_file}\n"
        message += f"⏰ Убакыт: {datetime.now ().strftime ( '%d.%m.%Y %H:%M' )}\n"

        self.send_telegram ( message )