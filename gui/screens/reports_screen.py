from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.graphics import Color, RoundedRectangle, Line
from datetime import datetime, timedelta
import threading


class ReportsScreen ( BoxLayout ):
    """Профессионалдык отчет бөлүмү"""

    def __init__(self, user_data, report_manager, analytics_manager, on_back, **kwargs):
        super ().__init__ ( **kwargs )
        self.orientation = 'vertical'
        self.user_data = user_data
        self.report_manager = report_manager
        self.analytics_manager = analytics_manager
        self.on_back = on_back
        self.selected_user_id = None
        self.user_ids = {}
        self.is_loading = False
        self.current_report_data = None
        self.selected_period = "day"  # day, month, year

        self.init_ui ()
        self.load_users ()
        Clock.schedule_once ( lambda dt: self.load_full_report ( None ), 0.5 )

    def init_ui(self):
        """Интерфейсти түзүү"""
        self.create_header ()
        self.create_filter_panel ()
        self.create_period_selector ()
        self.create_stats_dashboard ()
        self.create_chart_tabs ()
        self.create_details_panel ()
        self.create_export_panel ()
        self.create_status_bar ()

    def create_header(self):
        """Күчтүү башкы панель"""
        header = BoxLayout ( size_hint_y=0.07, padding=[15, 10, 15, 10], spacing=15 )
        with header.canvas.before:
            Color ( 0.1, 0.25, 0.45, 1 )
            self.header_rect = RoundedRectangle ( size=header.size, pos=header.pos, radius=[12] )
            header.bind ( pos=self.update_rect, size=self.update_rect )

        back_btn = Button (
            text="← БАШКЫ МЕНЮ",
            size_hint_x=0.13,
            background_color=(0.3, 0.45, 0.6, 1),
            font_size=12,
            bold=True
        )
        back_btn.bind ( on_press=lambda x: self.on_back () )
        header.add_widget ( back_btn )

        title = Label ( text="📊 ПРОФЕССИОНАЛДЫК ОТЧЕТ СИСТЕМАСЫ", color=(1, 1, 1, 1), font_size=18, bold=True )
        header.add_widget ( title )

        refresh_btn = Button (
            text="🔄",
            size_hint_x=0.08,
            background_color=(0.2, 0.5, 0.8, 1),
            font_size=16,
            bold=True
        )
        refresh_btn.bind ( on_press=self.refresh_all )
        header.add_widget ( refresh_btn )

        self.add_widget ( header )

    def create_period_selector(self):
        """Мезгил тандоо панели (күн, ай, жыл)"""
        period_card = BoxLayout ( size_hint_y=0.06, padding=8, spacing=10 )
        with period_card.canvas.before:
            Color ( 0.96, 0.96, 0.96, 1 )
            RoundedRectangle ( size=period_card.size, pos=period_card.pos, radius=[10] )
        period_card.bind ( pos=self.update_rect, size=self.update_rect )

        period_card.add_widget ( Label ( text="📆 ОТЧЕТ МЕЗГИЛИ:", size_hint_x=0.2, font_size=12, bold=True ) )

        self.day_btn = Button (
            text="📅 КҮНДҮК",
            size_hint_x=0.25,
            background_color=(0.25, 0.55, 0.85, 1),
            font_size=11,
            bold=True
        )
        self.day_btn.bind ( on_press=lambda x: self.set_period ( "day" ) )
        period_card.add_widget ( self.day_btn )

        self.month_btn = Button (
            text="📆 АЙЛЫК",
            size_hint_x=0.25,
            background_color=(0.85, 0.85, 0.85, 1),
            font_size=11,
            bold=True
        )
        self.month_btn.bind ( on_press=lambda x: self.set_period ( "month" ) )
        period_card.add_widget ( self.month_btn )

        self.year_btn = Button (
            text="📅 ЖЫЛДЫК",
            size_hint_x=0.25,
            background_color=(0.85, 0.85, 0.85, 1),
            font_size=11,
            bold=True
        )
        self.year_btn.bind ( on_press=lambda x: self.set_period ( "year" ) )
        period_card.add_widget ( self.year_btn )

        self.add_widget ( period_card )

    def set_period(self, period):
        """Отчет мезгилин тандоо"""
        self.selected_period = period

        # Кнопкалардын түсүн өзгөртүү
        self.day_btn.background_color = (0.85, 0.85, 0.85, 1)
        self.month_btn.background_color = (0.85, 0.85, 0.85, 1)
        self.year_btn.background_color = (0.85, 0.85, 0.85, 1)

        if period == "day":
            self.day_btn.background_color = (0.25, 0.55, 0.85, 1)
            self.set_quick_date ( 0 )
        elif period == "month":
            self.month_btn.background_color = (0.25, 0.55, 0.85, 1)
            self.set_month_date ()
        elif period == "year":
            self.year_btn.background_color = (0.25, 0.55, 0.85, 1)
            self.set_year_date ()

    def set_month_date(self):
        """Учурдагы айдын отчетун көрсөтүү"""
        today = datetime.now ()
        start = today.replace ( day=1 )
        self.start_date.text = start.strftime ( "%Y-%m-%d" )
        self.end_date.text = today.strftime ( "%Y-%m-%d" )
        self.load_full_report ( None )

    def set_year_date(self):
        """Учурдагы жылдын отчетун көрсөтүү"""
        today = datetime.now ()
        start = today.replace ( month=1, day=1 )
        self.start_date.text = start.strftime ( "%Y-%m-%d" )
        self.end_date.text = today.strftime ( "%Y-%m-%d" )
        self.load_full_report ( None )

    def create_filter_panel(self):
        """Күчтүү фильтр панели"""
        filter_card = BoxLayout ( orientation='vertical', size_hint_y=0.11, padding=12, spacing=6 )
        with filter_card.canvas.before:
            Color ( 0.98, 0.98, 0.98, 1 )
            RoundedRectangle ( size=filter_card.size, pos=filter_card.pos, radius=[12] )
            Line ( rectangle=(filter_card.x, filter_card.y, filter_card.width, filter_card.height), width=1,
                   color=(0.85, 0.85, 0.85, 1) )
        filter_card.bind ( pos=self.update_rect, size=self.update_rect )

        # 1-катар: Дата тандоо
        row1 = BoxLayout ( spacing=12, size_hint_y=0.5 )

        row1.add_widget ( Label ( text="📅 ДАТА ДИАПАЗОНУ:", size_hint_x=0.14, font_size=12, bold=True ) )

        self.start_date = TextInput (
            text=datetime.now ().strftime ( "%Y-%m-%d" ),
            size_hint_x=0.16,
            multiline=False,
            font_size=12,
            background_color=(1, 1, 1, 1),
            hint_text="YYYY-MM-DD"
        )
        row1.add_widget ( self.start_date )

        row1.add_widget ( Label ( text="→", size_hint_x=0.04, font_size=14 ) )

        self.end_date = TextInput (
            text=datetime.now ().strftime ( "%Y-%m-%d" ),
            size_hint_x=0.16,
            multiline=False,
            font_size=12,
            background_color=(1, 1, 1, 1),
            hint_text="YYYY-MM-DD"
        )
        row1.add_widget ( self.end_date )

        # Тез тандоо
        quick_btns = BoxLayout ( spacing=5, size_hint_x=0.46 )
        for text, days in [("БҮГҮН", 0), ("КЕЧЕ", 1), ("ЖУМА", 7), ("АЙ", 30), ("ЖЫЛ", 365)]:
            btn = Button ( text=text, size_hint_x=0.2, background_color=(0.25, 0.5, 0.75, 1), font_size=10, bold=True )
            btn.bind ( on_press=lambda x, d=days: self.set_quick_date ( d ) )
            quick_btns.add_widget ( btn )
        row1.add_widget ( quick_btns )
        filter_card.add_widget ( row1 )

        # 2-катар: Колдонуучу жана төлөм түрү
        row2 = BoxLayout ( spacing=12, size_hint_y=0.5 )

        row2.add_widget ( Label ( text="👤 КАССИР:", size_hint_x=0.1, font_size=12, bold=True ) )

        self.user_btn = Button (
            text="🏢 БАРДЫК КАССИРЛЕР",
            size_hint_x=0.25,
            background_color=(0.2, 0.45, 0.7, 1),
            font_size=11,
            bold=True
        )
        self.user_btn.bind ( on_press=self.show_user_menu )
        row2.add_widget ( self.user_btn )

        row2.add_widget ( Label ( text="💳 ТӨЛӨМ ТҮРҮ:", size_hint_x=0.12, font_size=12, bold=True ) )

        self.payment_filter = Button (
            text="БАРДЫК",
            size_hint_x=0.15,
            background_color=(0.35, 0.45, 0.55, 1),
            font_size=11
        )
        self.payment_filter.bind ( on_press=self.show_payment_menu )
        row2.add_widget ( self.payment_filter )

        self.search_btn = Button (
            text="🔍 ОТЧЕТТИ КӨРСӨТҮҮ",
            size_hint_x=0.18,
            background_color=(0.2, 0.7, 0.35, 1),
            font_size=12,
            bold=True
        )
        self.search_btn.bind ( on_press=self.load_full_report )
        row2.add_widget ( self.search_btn )

        filter_card.add_widget ( row2 )
        self.add_widget ( filter_card )

    def create_stats_dashboard(self):
        """Статистика дашборды - 5 карточка"""
        self.stats_grid = GridLayout ( cols=5, size_hint_y=0.18, spacing=10, padding=[10, 5, 10, 5] )
        self.add_widget ( self.stats_grid )

        self.stat_cards = {}
        stats = [
            ("total_sales", "📊 ЖАЛПЫ САТУУ", "0", "#2c3e50"),
            ("total_amount", "💰 ЖАЛПЫ СУММА", "0 сом", "#27ae60"),
            ("cash_amount", "💵 НАКТАЛАЙ", "0 сом", "#f39c12"),
            ("card_amount", "💳 КАРТА", "0 сом", "#2980b9"),
            ("credit_amount", "📝 НАСЫЯ", "0 сом", "#e74c3c")
        ]

        for key, title, default, color in stats:
            card = BoxLayout ( orientation='vertical', padding=8, spacing=3 )
            with card.canvas.before:
                Color ( *self.hex_to_rgb ( color ), 1 )
                RoundedRectangle ( size=card.size, pos=card.pos, radius=[10] )
            card.bind ( pos=self.update_rect, size=self.update_rect )

            card.add_widget ( Label ( text=title, font_size=11, color=(1, 1, 1, 0.9), bold=True ) )
            self.stat_cards[key] = Label ( text=default, font_size=20, bold=True, color=(1, 1, 1, 1) )
            card.add_widget ( self.stat_cards[key] )

            self.stats_grid.add_widget ( card )

    def create_chart_tabs(self):
        """Графиктер үчүн таб панель"""
        chart_card = BoxLayout ( orientation='vertical', size_hint_y=0.22, padding=8, spacing=6 )
        with chart_card.canvas.before:
            Color ( 0.96, 0.96, 0.96, 1 )
            RoundedRectangle ( size=chart_card.size, pos=chart_card.pos, radius=[12] )
        chart_card.bind ( pos=self.update_rect, size=self.update_rect )

        # Таб кнопкалары
        tab_layout = BoxLayout ( size_hint_y=0.2, spacing=8, padding=[5, 0, 5, 0] )
        tabs = [
            ("📈 КҮНДҮК АНАЛИТИКА", "daily"),
            ("📊 АЙЛЫК АНАЛИТИКА", "monthly"),
            ("📅 ЖЫЛДЫК АНАЛИТИКА", "yearly"),
            ("👥 КАССИРЛЕР РЕЙТИНГИ", "users"),
            ("🏆 ТОП 10 ТОВАР", "top")
        ]

        self.chart_buttons = {}
        for text, key in tabs:
            btn = Button ( text=text, size_hint_x=0.2, background_color=(0.85, 0.85, 0.85, 1), color=(0, 0, 0, 1),
                           font_size=10, bold=True )
            btn.bind ( on_press=lambda x, k=key: self.switch_chart ( k ) )
            tab_layout.add_widget ( btn )
            self.chart_buttons[key] = btn

        chart_card.add_widget ( tab_layout )

        # График контейнери
        self.chart_container = BoxLayout ( orientation='vertical', size_hint_y=0.8, padding=5 )
        self.chart_container.add_widget ( Label ( text="📊 Маалыматтарды көрсөтүү үчүн отчетту жүктөңүз", font_size=12,
                                                  color=(0.5, 0.5, 0.5, 1) ) )
        chart_card.add_widget ( self.chart_container )

        self.add_widget ( chart_card )
        self.current_chart = "daily"
        self.chart_buttons["daily"].background_color = (0.25, 0.55, 0.85, 1)
        self.chart_buttons["daily"].color = (1, 1, 1, 1)

    def create_details_panel(self):
        """Деталдуу маалыматтар панели"""
        details_card = BoxLayout ( orientation='vertical', size_hint_y=0.22, padding=10, spacing=5 )
        with details_card.canvas.before:
            Color ( 0.98, 0.98, 0.98, 1 )
            RoundedRectangle ( size=details_card.size, pos=details_card.pos, radius=[12] )
        details_card.bind ( pos=self.update_rect, size=self.update_rect )

        title_layout = BoxLayout ( size_hint_y=0.12 )
        title_layout.add_widget ( Label ( text="📋 ДЕТАЛДУУ МААЛЫМАТТАР", font_size=13, bold=True ) )
        details_card.add_widget ( title_layout )

        self.details_scroll = ScrollView ()
        self.details_content = BoxLayout ( orientation='vertical', size_hint_y=None, spacing=3 )
        self.details_content.bind ( minimum_height=self.details_content.setter ( 'height' ) )
        self.details_scroll.add_widget ( self.details_content )
        details_card.add_widget ( self.details_scroll )

        self.add_widget ( details_card )

    def create_export_panel(self):
        """Экспорт панели"""
        export_card = BoxLayout ( size_hint_y=0.05, padding=8, spacing=15 )
        with export_card.canvas.before:
            Color ( 0.94, 0.94, 0.94, 1 )
            RoundedRectangle ( size=export_card.size, pos=export_card.pos, radius=[10] )
        export_card.bind ( pos=self.update_rect, size=self.update_rect )

        pdf_btn = Button (
            text="📄 PDF ОТЧЕТ",
            size_hint_x=0.25,
            background_color=(0.8, 0.25, 0.25, 1),
            font_size=12,
            bold=True
        )
        pdf_btn.bind ( on_press=self.export_pdf )
        export_card.add_widget ( pdf_btn )

        excel_btn = Button (
            text="📊 EXCEL ОТЧЕТ",
            size_hint_x=0.25,
            background_color=(0.25, 0.65, 0.25, 1),
            font_size=12,
            bold=True
        )
        excel_btn.bind ( on_press=self.export_excel )
        export_card.add_widget ( excel_btn )

        export_card.add_widget (
            Label ( text="📁 reports/ папкасына сакталат", font_size=10, color=(0.5, 0.5, 0.5, 1) ) )

        self.add_widget ( export_card )

    def create_status_bar(self):
        """Статус бара"""
        self.status_bar = BoxLayout ( size_hint_y=0.03, padding=[10, 2, 10, 2] )
        with self.status_bar.canvas.before:
            Color ( 0.25, 0.3, 0.35, 1 )
            RoundedRectangle ( size=self.status_bar.size, pos=self.status_bar.pos, radius=[5] )
        self.status_bar.bind ( pos=self.update_rect, size=self.update_rect )

        self.status_label = Label ( text="✅ Система даяр", color=(0.85, 0.85, 0.85, 1), font_size=10, halign='left' )
        self.status_bar.add_widget ( self.status_label )

        self.add_widget ( self.status_bar )

    def update_rect(self, instance, value):
        try:
            for child in instance.canvas.before.children:
                if hasattr ( child, 'size' ) and hasattr ( child, 'pos' ):
                    child.size = instance.size
                    child.pos = instance.pos
                    break
        except:
            pass

    def hex_to_rgb(self, hex_color):
        hex_color = hex_color.lstrip ( '#' )
        return tuple ( int ( hex_color[i:i + 2], 16 ) / 255.0 for i in (0, 2, 4) )

    def set_quick_date(self, days):
        try:
            end = datetime.now ()
            start = end - timedelta ( days=days )
            self.start_date.text = start.strftime ( "%Y-%m-%d" )
            self.end_date.text = end.strftime ( "%Y-%m-%d" )
            self.load_full_report ( None )
        except Exception as err:
            print ( f"Quick date error: {err}" )
            today = datetime.now ().strftime ( "%Y-%m-%d" )
            self.start_date.text = today
            self.end_date.text = today

    def load_users(self):
        try:
            from database.db_manager import DatabaseManager
            from database.models import User

            db = DatabaseManager ()
            session = db.get_session ()
            users = session.query ( User ).filter_by ( is_active=True ).all ()

            self.user_list = []
            self.user_ids = {}
            self.user_ids["🏢 БАРДЫК КАССИРЛЕР"] = None

            for user in users:
                icon = "👑" if user.role.value == "admin" else "💼" if user.role.value == "manager" else "🛒"
                name = f"{icon} {user.full_name}"
                self.user_list.append ( name )
                self.user_ids[name] = user.id

            session.close ()
        except Exception as e:
            print ( f"Load users error: {e}" )

    def show_user_menu(self, instance):
        content = BoxLayout ( orientation='vertical', spacing=5, padding=10 )

        scroll = ScrollView ()
        list_layout = BoxLayout ( orientation='vertical', size_hint_y=None, spacing=3 )
        list_layout.bind ( minimum_height=list_layout.setter ( 'height' ) )

        all_btn = Button ( text="🏢 БАРДЫК КАССИРЛЕР", size_hint_y=None, height=45, background_color=(0.2, 0.5, 0.8, 1),
                           font_size=13 )
        all_btn.bind ( on_press=lambda x: self.select_user ( "🏢 БАРДЫК КАССИРЛЕР", None ) )
        list_layout.add_widget ( all_btn )

        for name in self.user_list:
            user_btn = Button ( text=name, size_hint_y=None, height=45, background_color=(0.95, 0.95, 0.95, 1),
                                color=(0, 0, 0, 1), font_size=12 )
            user_btn.bind ( on_press=lambda x, n=name: self.select_user ( n, self.user_ids.get ( n ) ) )
            list_layout.add_widget ( user_btn )

        scroll.add_widget ( list_layout )
        content.add_widget ( scroll )

        close_btn = Button ( text="ЖАБУУ", size_hint_y=0.1, background_color=(0.5, 0.5, 0.5, 1), font_size=12 )
        content.add_widget ( close_btn )

        popup = Popup ( title="👥 КАССИРДИ ТАНДАҢЫЗ", content=content, size_hint=(0.5, 0.65) )
        close_btn.bind ( on_press=popup.dismiss )
        popup.open ()

    def show_payment_menu(self, instance):
        content = BoxLayout ( orientation='vertical', spacing=5, padding=10 )

        for text in ["БАРДЫК", "💵 НАКТАЛАЙ", "💳 КАРТА", "📝 НАСЫЯ"]:
            btn = Button ( text=text, size_hint_y=None, height=45, font_size=12 )
            btn.bind ( on_press=lambda x, t=text: self.select_payment ( t ) )
            content.add_widget ( btn )

        close_btn = Button ( text="ЖАБУУ", size_hint_y=0.1, background_color=(0.5, 0.5, 0.5, 1) )
        content.add_widget ( close_btn )

        popup = Popup ( title="💳 ТӨЛӨМ ТҮРҮ", content=content, size_hint=(0.4, 0.4) )
        close_btn.bind ( on_press=popup.dismiss )
        popup.open ()

    def select_user(self, name, user_id):
        self.user_btn.text = name
        self.selected_user_id = user_id
        self.load_full_report ( None )

    def select_payment(self, payment):
        self.payment_filter.text = payment
        self.load_full_report ( None )

    def refresh_all(self, instance):
        self.load_full_report ( None )

    def set_status(self, text, status_type="info"):
        colors = {"info": (0.25, 0.3, 0.35, 1), "success": (0.2, 0.7, 0.2, 1), "error": (0.8, 0.2, 0.2, 1),
                  "loading": (0.8, 0.6, 0.2, 1)}
        self.status_label.text = text
        with self.status_bar.canvas.before:
            Color ( *colors.get ( status_type, (0.25, 0.3, 0.35, 1) ), 1 )
            RoundedRectangle ( size=self.status_bar.size, pos=self.status_bar.pos, radius=[5] )

    def load_full_report(self, instance):
        if self.is_loading:
            return

        self.is_loading = True
        self.set_status ( "📊 Отчет жүктөлүүдө...", "loading" )

        def load():
            try:
                start = datetime.strptime ( self.start_date.text, "%Y-%m-%d" )
                end = datetime.strptime ( self.end_date.text, "%Y-%m-%d" )
                end = end.replace ( hour=23, minute=59, second=59 )

                payment_filter = self.payment_filter.text
                payment_type = None
                if payment_filter != "БАРДЫК":
                    payment_map = {"💵 НАКТАЛАЙ": "cash", "💳 КАРТА": "card", "📝 НАСЫЯ": "credit"}
                    payment_type = payment_map.get ( payment_filter )

                total_summary = self.report_manager.get_sales_summary ( start, end )
                users_report = self.report_manager.get_all_users_report ( start, end )

                user_report = None
                if self.selected_user_id:
                    user_report = self.report_manager.get_user_weekly_report ( self.selected_user_id, start, end )

                days = (end - start).days
                if days <= 0:
                    days = 1
                top_products = self.analytics_manager.get_top_products ( 10, days )

                daily_data = self.get_daily_sales_data ( start, end, self.selected_user_id, payment_type )
                monthly_data = self.get_monthly_sales_data ( start, end, self.selected_user_id, payment_type )
                yearly_data = self.get_yearly_sales_data ( start, end, self.selected_user_id, payment_type )
                hourly_data = self.get_hourly_sales_data ( start, end, self.selected_user_id, payment_type )

                self.current_report_data = {
                    'summary': total_summary,
                    'users': users_report,
                    'user_report': user_report,
                    'top_products': top_products,
                    'daily': daily_data,
                    'monthly': monthly_data,
                    'yearly': yearly_data,
                    'hourly': hourly_data,
                    'start': start,
                    'end': end
                }

                Clock.schedule_once ( lambda dt: self.update_ui (), 0 )

            except Exception as e:
                print ( f"Load error: {e}" )
                import traceback
                traceback.print_exc ()
                Clock.schedule_once ( lambda dt: self.set_status ( f"❌ Ката: {e}", "error" ), 0 )
            finally:
                Clock.schedule_once ( lambda dt: setattr ( self, 'is_loading', False ), 0 )

        threading.Thread ( target=load, daemon=True ).start ()

    def get_daily_sales_data(self, start, end, user_id, payment_type):
        session = self.report_manager.get_session ()
        try:
            from database.models import Sale, SaleItem
            from sqlalchemy import func

            start_date = datetime ( start.year, start.month, start.day, 0, 0, 0 )
            end_date = datetime ( end.year, end.month, end.day, 23, 59, 59 )

            query = session.query (
                func.date ( Sale.created_at ).label ( 'date' ),
                func.count ( Sale.id ).label ( 'count' ),
                func.sum ( Sale.total_amount ).label ( 'total' ),
                func.sum ( SaleItem.quantity ).label ( 'items' )
            ).join ( SaleItem, SaleItem.sale_id == Sale.id )

            if user_id:
                query = query.filter ( Sale.user_id == user_id )
            if payment_type:
                query = query.filter ( Sale.payment_type == payment_type )

            query = query.filter (
                Sale.created_at >= start_date,
                Sale.created_at <= end_date
            ).group_by ( func.date ( Sale.created_at ) ).order_by ( func.date ( Sale.created_at ) )

            return query.all ()
        finally:
            session.close ()

    def get_monthly_sales_data(self, start, end, user_id, payment_type):
        """Айлык сатуу маалыматтарын алуу"""
        session = self.report_manager.get_session ()
        try:
            from database.models import Sale, SaleItem
            from sqlalchemy import func

            query = session.query (
                func.strftime ( '%Y-%m', Sale.created_at ).label ( 'month' ),
                func.count ( Sale.id ).label ( 'count' ),
                func.sum ( Sale.total_amount ).label ( 'total' ),
                func.sum ( SaleItem.quantity ).label ( 'items' )
            ).join ( SaleItem, SaleItem.sale_id == Sale.id )

            if user_id:
                query = query.filter ( Sale.user_id == user_id )
            if payment_type:
                query = query.filter ( Sale.payment_type == payment_type )

            query = query.filter (
                Sale.created_at >= start,
                Sale.created_at <= end
            ).group_by ( 'month' ).order_by ( 'month' )

            return query.all ()
        finally:
            session.close ()

    def get_yearly_sales_data(self, start, end, user_id, payment_type):
        """Жылдык сатуу маалыматтарын алуу"""
        session = self.report_manager.get_session ()
        try:
            from database.models import Sale, SaleItem
            from sqlalchemy import func

            query = session.query (
                func.strftime ( '%Y', Sale.created_at ).label ( 'year' ),
                func.count ( Sale.id ).label ( 'count' ),
                func.sum ( Sale.total_amount ).label ( 'total' ),
                func.sum ( SaleItem.quantity ).label ( 'items' )
            ).join ( SaleItem, SaleItem.sale_id == Sale.id )

            if user_id:
                query = query.filter ( Sale.user_id == user_id )
            if payment_type:
                query = query.filter ( Sale.payment_type == payment_type )

            query = query.filter (
                Sale.created_at >= start,
                Sale.created_at <= end
            ).group_by ( 'year' ).order_by ( 'year' )

            return query.all ()
        finally:
            session.close ()

    def get_hourly_sales_data(self, start, end, user_id, payment_type):
        session = self.report_manager.get_session ()
        try:
            from database.models import Sale
            from sqlalchemy import func

            start_date = datetime ( start.year, start.month, start.day, 0, 0, 0 )
            end_date = datetime ( end.year, end.month, end.day, 23, 59, 59 )

            query = session.query (
                func.strftime ( '%H', Sale.created_at ).label ( 'hour' ),
                func.count ( Sale.id ).label ( 'count' ),
                func.sum ( Sale.total_amount ).label ( 'total' )
            )

            if user_id:
                query = query.filter ( Sale.user_id == user_id )
            if payment_type:
                query = query.filter ( Sale.payment_type == payment_type )

            query = query.filter (
                Sale.created_at >= start_date,
                Sale.created_at <= end_date
            ).group_by ( 'hour' ).order_by ( 'hour' )

            return query.all ()
        finally:
            session.close ()

    def update_ui(self):
        if not self.current_report_data:
            return

        data = self.current_report_data
        summary = data['summary']

        self.stat_cards['total_sales'].text = f"{summary['total_sales']}"
        self.stat_cards['total_amount'].text = f"{summary['total_amount']:,.0f} сом"
        self.stat_cards['cash_amount'].text = f"{summary['cash_amount']:,.0f} сом"
        self.stat_cards['card_amount'].text = f"{summary['card_amount']:,.0f} сом"
        self.stat_cards['credit_amount'].text = f"{summary['credit_amount']:,.0f} сом"

        self.switch_chart ( self.current_chart )
        self.update_details_panel ( data )

        period_text = ""
        if self.selected_period == "day":
            period_text = "КҮНДҮК"
        elif self.selected_period == "month":
            period_text = "АЙЛЫК"
        else:
            period_text = "ЖЫЛДЫК"

        self.set_status (
            f"✅ {period_text} отчет жүктөлдү: {data['start'].strftime ( '%d.%m.%Y' )} - {data['end'].strftime ( '%d.%m.%Y' )}",
            "success" )

    def switch_chart(self, chart_type):
        self.current_chart = chart_type

        for key, btn in self.chart_buttons.items ():
            btn.background_color = (0.85, 0.85, 0.85, 1)
            btn.color = (0, 0, 0, 1)

        self.chart_buttons[chart_type].background_color = (0.25, 0.55, 0.85, 1)
        self.chart_buttons[chart_type].color = (1, 1, 1, 1)

        if not self.current_report_data:
            return

        data = self.current_report_data
        self.chart_container.clear_widgets ()

        if chart_type == "daily" and data.get ( 'daily' ):
            self.show_period_chart ( data['daily'], "Күндүк" )
        elif chart_type == "monthly" and data.get ( 'monthly' ):
            self.show_period_chart ( data['monthly'], "Айлык" )
        elif chart_type == "yearly" and data.get ( 'yearly' ):
            self.show_period_chart ( data['yearly'], "Жылдык" )
        elif chart_type == "users" and data['users'] and data['users'].get ( 'users' ):
            self.show_users_chart ( data['users']['users'] )
        elif chart_type == "top" and data.get ( 'top_products' ):
            self.show_top_products_chart ( data['top_products'] )
        else:
            self.chart_container.add_widget ( Label ( text="📊 Маалымат жок", font_size=12, color=(0.5, 0.5, 0.5, 1) ) )

    def show_period_chart(self, period_data, period_name):
        """Күндүк, айлык, жылдык графиктерди көрсөтүү"""
        content = BoxLayout ( orientation='vertical', spacing=5 )

        if not period_data:
            content.add_widget (
                Label ( text=f"📊 {period_name} маалыматтар жок", font_size=12, color=(0.5, 0.5, 0.5, 1) ) )
        else:
            for d in period_data:
                row = BoxLayout ( size_hint_y=None, height=38, spacing=8 )
                row.add_widget ( Label ( text=d[0], font_size=11, size_hint_x=0.3, bold=True ) )
                row.add_widget ( Label ( text=f"🛒 {d[1]}", font_size=11, size_hint_x=0.2, halign='center' ) )
                row.add_widget ( Label ( text=f"💰 {d[2]:.0f} сом", font_size=11, size_hint_x=0.3, halign='right',
                                         color=(0, 0.6, 0, 1) ) )
                if len ( d ) > 3:
                    row.add_widget ( Label ( text=f"📦 {d[3]}", font_size=11, size_hint_x=0.2, halign='right' ) )
                content.add_widget ( row )

        scroll = ScrollView ()
        scroll.add_widget ( content )
        self.chart_container.add_widget ( scroll )

    def show_users_chart(self, users_data):
        content = BoxLayout ( orientation='vertical', spacing=5 )
        for user in users_data:
            row = BoxLayout ( size_hint_y=None, height=42, spacing=8 )
            icon = "👑" if user.role.value == "admin" else "💼" if user.role.value == "manager" else "🛒"
            row.add_widget ( Label ( text=f"{icon} {user.full_name}", font_size=12, size_hint_x=0.42, bold=True ) )
            row.add_widget (
                Label ( text=f"🛒 {user.sale_count or 0}", font_size=12, size_hint_x=0.18, halign='center' ) )
            row.add_widget (
                Label ( text=f"💰 {(user.total_amount or 0):,.0f} сом", font_size=12, size_hint_x=0.4, halign='right',
                        color=(0, 0.6, 0, 1) ) )
            content.add_widget ( row )

        scroll = ScrollView ()
        scroll.add_widget ( content )
        self.chart_container.add_widget ( scroll )

    def show_top_products_chart(self, products):
        content = BoxLayout ( orientation='vertical', spacing=5 )
        for i, p in enumerate ( products[:10], 1 ):
            row = BoxLayout ( size_hint_y=None, height=42, spacing=8 )
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            product_name = p[0] if len ( p ) > 0 and p[0] else "Аталышы жок"
            quantity = p[1] if len ( p ) > 1 else 0
            amount = p[2] if len ( p ) > 2 else 0

            row.add_widget ( Label ( text=f"{medal} {product_name}", font_size=11, size_hint_x=0.55 ) )
            row.add_widget ( Label ( text=f"{quantity:.0f} даана", font_size=11, size_hint_x=0.2, halign='center' ) )
            row.add_widget ( Label ( text=f"{amount:.0f} сом", font_size=11, size_hint_x=0.25, halign='right',
                                     color=(0, 0.6, 0, 1) ) )
            content.add_widget ( row )

        scroll = ScrollView ()
        scroll.add_widget ( content )
        self.chart_container.add_widget ( scroll )

    def update_details_panel(self, data):
        self.details_content.clear_widgets ()

        info_row = BoxLayout ( size_hint_y=None, height=32, spacing=8 )
        info_row.add_widget ( Label (
            text=f"📅 Отчет мезгили: {data['start'].strftime ( '%d.%m.%Y' )} - {data['end'].strftime ( '%d.%m.%Y' )}",
            font_size=11 ) )
        self.details_content.add_widget ( info_row )

        info_row2 = BoxLayout ( size_hint_y=None, height=32, spacing=8 )
        info_row2.add_widget ( Label ( text=f"👤 Кассир: {self.user_btn.text}", font_size=11 ) )
        info_row2.add_widget ( Label ( text=f"💳 Төлөм түрү: {self.payment_filter.text}", font_size=11 ) )
        self.details_content.add_widget ( info_row2 )

        line = BoxLayout ( size_hint_y=None, height=2, padding=0 )
        with line.canvas.before:
            Color ( 0.8, 0.8, 0.8, 1 )
            RoundedRectangle ( size=line.size, pos=line.pos, radius=[0] )
        self.details_content.add_widget ( line )

        if data['user_report']:
            ur = data['user_report']
            self.details_content.add_widget (
                Label ( text=f"📊 {self.user_btn.text} үчүн деталдар:", font_size=12, bold=True ) )

            stat_row = BoxLayout ( size_hint_y=None, height=35, spacing=10 )
            stat_row.add_widget ( Label ( text=f"🛒 Сатуулар: {ur['total_sales']}", font_size=11 ) )
            stat_row.add_widget (
                Label ( text=f"💰 Сумма: {ur['total_amount']:.0f} сом", font_size=11, color=(0, 0.6, 0, 1) ) )
            stat_row.add_widget ( Label ( text=f"📦 Товарлар: {ur['total_items']}", font_size=11 ) )
            self.details_content.add_widget ( stat_row )

    def export_pdf(self, instance):
        if not self.current_report_data:
            self.set_status ( "❌ Алгач отчетту жүктөңүз", "error" )
            return

        self.set_status ( "📄 PDF отчет түзүлүүдө...", "loading" )

        def export():
            try:
                data = self.current_report_data
                period = self.selected_period
                filename = f"report_{period}_{data['start'].strftime ( '%Y%m%d' )}_{data['end'].strftime ( '%Y%m%d' )}.pdf"

                if self.selected_user_id:
                    result = self.report_manager.generate_user_pdf_report ( self.selected_user_id, data['start'],
                                                                            data['end'], filename )
                else:
                    result = self.report_manager.generate_pdf_report ( data['start'], data['end'], filename )

                if result:
                    Clock.schedule_once ( lambda dt: self.set_status ( f"✅ PDF отчет түзүлдү: {filename}", "success" ),
                                          0 )
                else:
                    Clock.schedule_once ( lambda dt: self.set_status ( "❌ PDF отчет түзүлүүдө ката", "error" ), 0 )
            except Exception as e:
                print ( f"PDF export error: {e}" )
                Clock.schedule_once ( lambda dt: self.set_status ( f"❌ Ката: {e}", "error" ), 0 )

        threading.Thread ( target=export, daemon=True ).start ()

    def export_excel(self, instance):
        if not self.current_report_data:
            self.set_status ( "❌ Алгач отчетту жүктөңүз", "error" )
            return

        self.set_status ( "📊 Excel отчет түзүлүүдө...", "loading" )

        def export():
            try:
                data = self.current_report_data
                period = self.selected_period
                filename = f"report_{period}_{data['start'].strftime ( '%Y%m%d' )}_{data['end'].strftime ( '%Y%m%d' )}.xlsx"
                result = self.report_manager.generate_excel_report ( data['start'], data['end'], filename )

                if result:
                    Clock.schedule_once (
                        lambda dt: self.set_status ( f"✅ Excel отчет түзүлдү: {filename}", "success" ),
                        0 )
                else:
                    Clock.schedule_once ( lambda dt: self.set_status ( "❌ Excel отчет түзүлүүдө ката", "error" ), 0 )
            except Exception as e:
                print ( f"Excel export error: {e}" )
                Clock.schedule_once ( lambda dt: self.set_status ( f"❌ Ката: {e}", "error" ), 0 )

        threading.Thread ( target=export, daemon=True ).start ()