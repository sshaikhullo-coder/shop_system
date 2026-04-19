from database.db_manager import DatabaseManager
from database.models import User, UserRole
import hashlib
from datetime import datetime


class AuthManager:
    def __init__(self):
        self.db = DatabaseManager ()
        self.current_user_data = None

    def get_session(self):
        return self.db.get_session ()

    def login(self, username, password):
        """Кирүү функциясы - username жана password гана күтөт"""
        session = self.get_session ()
        try:
            hashed_pwd = hashlib.sha256 ( password.encode () ).hexdigest ()
            user = session.query ( User ).filter_by (
                username=username,
                password=hashed_pwd,
                is_active=True
            ).first ()

            if user:
                user.last_login = datetime.now ()
                session.commit ()
                self.current_user_data = {
                    'id': user.id,
                    'username': user.username,
                    'full_name': user.full_name,
                    'role': user.role,
                    'is_active': user.is_active
                }
                return True, self.current_user_data
            return False, "Колдонуучу аты же сырсөз туура эмес"
        except Exception as e:
            return False, str ( e )
        finally:
            session.close ()

    def logout(self):
        self.current_user_data = None

    def is_admin(self):
        return self.current_user_data and self.current_user_data['role'] == UserRole.ADMIN

    def is_manager(self):
        return self.current_user_data and self.current_user_data['role'] in [UserRole.ADMIN, UserRole.MANAGER]

    def get_current_user(self):
        return self.current_user_data

    def has_permission(self, permission_type):
        if not self.current_user_data:
            return False
        if self.current_user_data['role'] == UserRole.ADMIN:
            return True
        if permission_type == "sale":
            return self.current_user_data['role'] == UserRole.CASHIER
        if permission_type == "report":
            return self.current_user_data['role'] in [UserRole.CASHIER, UserRole.MANAGER]
        return False

    def add_user(self, username, password, full_name, role):
        if not self.is_admin ():
            return False, "Уруксат жок"

        session = self.get_session ()
        try:
            existing = session.query ( User ).filter_by ( username=username ).first ()
            if existing:
                return False, "Бул колдонуучу аты бар"

            user = User (
                username=username,
                password=hashlib.sha256 ( password.encode () ).hexdigest (),
                full_name=full_name,
                role=UserRole ( role )
            )
            session.add ( user )
            session.commit ()
            return True, user
        except Exception as e:
            session.rollback ()
            return False, str ( e )
        finally:
            session.close ()

    def get_all_users(self):
        if not self.is_admin ():
            return []

        session = self.get_session ()
        try:
            users = session.query ( User ).all ()
            users_data = []
            for user in users:
                users_data.append ( {
                    'id': user.id,
                    'username': user.username,
                    'full_name': user.full_name,
                    'role': user.role,
                    'is_active': user.is_active,
                    'last_login': user.last_login
                } )
            return users_data
        finally:
            session.close ()

    def update_user(self, user_id, **kwargs):
        if not self.is_admin ():
            return False, "Уруксат жок"

        session = self.get_session ()
        try:
            user = session.query ( User ).filter_by ( id=user_id ).first ()
            if user:
                for key, value in kwargs.items ():
                    if key == 'password':
                        value = hashlib.sha256 ( value.encode () ).hexdigest ()
                    if hasattr ( user, key ):
                        setattr ( user, key, value )
                session.commit ()
                return True, "Жаңыртылды"
            return False, "Колдонуучу табылган жок"
        except Exception as e:
            session.rollback ()
            return False, str ( e )
        finally:
            session.close ()

    def delete_user(self, user_id):
        if not self.is_admin ():
            return False, "Уруксат жок"

        if self.current_user_data and self.current_user_data['id'] == user_id:
            return False, "Өзүңүздү өчүрө албайсыз"

        session = self.get_session ()
        try:
            user = session.query ( User ).filter_by ( id=user_id ).first ()
            if user:
                session.delete ( user )
                session.commit ()
                return True, "Өчүрүлдү"
            return False, "Колдонуучу табылган жок"
        except Exception as e:
            session.rollback ()
            return False, str ( e )
        finally:
            session.close ()