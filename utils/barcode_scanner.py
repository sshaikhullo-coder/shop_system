"""
Штрихкод сканерлеу модулу
"""

import logging
from kivy.clock import Clock

logger = logging.getLogger ( __name__ )


class BarcodeScanner:
    """Штрихкод сканерлеу классы"""

    def __init__(self):
        self.scanned_data = None
        self.scan_callback = None
        self.scanning = False
        self.buffer = ""
        self.last_key_time = 0
        logger.info ( "Штрихкод сканер инициализацияланды" )

    def start_scanning(self, callback=None):
        """
        Сканерлөөнү баштоо

        Args:
            callback (callable): Сканерленген маалыматты кайтаруучу функция
        """
        self.scanning = True
        self.scan_callback = callback
        self.buffer = ""
        logger.info ( "Штрихкод сканерлөө башталды" )

    def stop_scanning(self):
        """Сканерлөөнү токтотуу"""
        self.scanning = False
        self.scan_callback = None
        self.buffer = ""
        logger.info ( "Штрихкод сканерлөө токтотулду" )

    def process_key(self, key):
        """
        Клавиатурадан келген кодду иштетүү

        Args:
            key (str): Басылган клавиша
        """
        if not self.scanning:
            return

        import time
        current_time = time.time ()

        # Эгер клавишалардын ортосунда 50мс өтсө, жаңы сканер деп эсептейбиз
        if current_time - self.last_key_time > 0.05:
            self.buffer = ""

        self.last_key_time = current_time

        if key == 'enter' or key == '\r' or key == '\n':
            # Сканер аяктады
            if self.buffer and self.scan_callback:
                logger.info ( f"Штрихкод сканерленди: {self.buffer}" )
                Clock.schedule_once ( lambda dt: self.scan_callback ( self.buffer ), 0 )
            self.buffer = ""
        else:
            self.buffer += key

    def simulate_scan(self, barcode):
        """
        Сканерлөөнү симуляциялоо (тестирлөө үчүн)

        Args:
            barcode (str): Штрихкод номери

        Returns:
            str: Сканерленген штрихкод
        """
        self.scanned_data = barcode
        if self.scan_callback:
            Clock.schedule_once ( lambda dt: self.scan_callback ( barcode ), 0 )
        logger.info ( f"Симуляцияланган сканер: {barcode}" )
        return barcode

    def get_scanned_data(self):
        """
        Сканерленген маалыматты алуу

        Returns:
            str: Сканерленген маалымат, же None
        """
        data = self.scanned_data
        self.scanned_data = None
        return data

    def generate_test_barcode(self, product_id):
        """
        Тест үчүн штрихкод түзүү

        Args:
            product_id (int): Товар ID

        Returns:
            str: Жасалма штрихкод
        """
        return f"TEST{product_id:06d}"