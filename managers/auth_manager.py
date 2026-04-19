"""
Аутентификация менеджери
Колдонуучуларды башкаруу жана кирүү
"""

import hashlib
from typing import Optional, Dict, List, Tuple
from database.db_manager import DatabaseManager
from database.models import User


class AuthManager:
    """Аутентификация жана колдонуучуларды башкаруу"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def _hash_password(self, password: str) -> str:
        """Парольду хэштөө"""
        return hashlib.sha256 ( password.encode () ).hexdigest ()

    def register_user(self, username: str, password: str, full_name: str, role: str = 'cashier') -> Tuple[bool, str]:
        """Жаңы колдонуучу каттоо"""
        try:
            if not username or not password or not full_name:
                return False, "Бардык талааларды толтуруңуз!"

            if len ( password ) < 4:
                return False, "Пароль 4 символдон кем болбошу керек!"

            hashed_password = self._hash_password ( password )
            success, result = self.db.add_user ( username, hashed_password, full_name, role )
            return success, result if success else result

        except Exception as e:
            return False, f"Каттоо катасы: {str ( e )}"

    def login(self, username: str, password: str) -> Tuple[bool, Optional[Dict]]:
        """Системага кирүү"""
        try:
            user = self.db.get_user_by_username ( username )

            if not user:
                return False, "Колдонуучу табылган жок!"

            if not user.is_active:
                return False, "Колдонуучу бөгөттөлгөн!"

            hashed_password = self._hash_password ( password )

            if user.password != hashed_password:
                return False, "Пароль туура эмес!"

            # Акыркы кирүү убактысын жаңыртуу
            self.db.update_last_login ( user.id )

            user_data = {
                'id': user.id,
                'username': user.username,
                'full_name': user.full_name,
                'role': user.role
            }

            return True, user_data

        except Exception as e:
            return False, f"Кирүү катасы: {str ( e )}"

    def get_all_users(self) -> List[User]:
        """Бардык колдонуучуларды алуу"""
        return self.db.get_all_users ()

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """ID боюнча колдонуучу алуу"""
        users = self.db.get_all_users ()
        for user in users:
            if user.id == user_id:
                return user
        return None

    def get_user_by_username(self, username: str) -> Optional[User]:
        """Колдонуучу аты боюнча колдонуучу алуу"""
        return self.db.get_user_by_username ( username )

    def update_user(self, user_id: int, **kwargs) -> Tuple[bool, str]:
        """Колдонуучуну жаңыртуу"""
        try:
            # Эгер пароль өзгөрсө, хэштеө
            if 'password' in kwargs and kwargs['password']:
                kwargs['password'] = self._hash_password ( kwargs['password'] )
            elif 'password' in kwargs:
                del kwargs['password']

            return self.db.update_user ( user_id, **kwargs )

        except Exception as e:
            return False, f"Жаңыртуу катасы: {str ( e )}"

    def delete_user(self, user_id: int) -> Tuple[bool, str]:
        """Колдонуучуну өчүрүү"""
        return self.db.delete_user ( user_id )

    def change_password(self, user_id: int, old_password: str, new_password: str) -> Tuple[bool, str]:
        """Пароль өзгөртүү"""
        try:
            user = self.get_user_by_id ( user_id )
            if not user:
                return False, "Колдонуучу табылган жок!"

            if self._hash_password ( old_password ) != user.password:
                return False, "Эски пароль туура эмес!"

            if len ( new_password ) < 4:
                return False, "Жаңы пароль 4 символдон кем болбошу керек!"

            return self.update_user ( user_id, password=new_password )

        except Exception as e:
            return False, f"Пароль өзгөртүү катасы: {str ( e )}"

    def has_permission(self, user_role: str, required_role: str) -> bool:
        """Укуктарды текшерүү"""
        permissions = {
            'admin': ['view', 'edit', 'delete', 'manage_users'],
            'manager': ['view', 'edit', 'delete'],
            'cashier': ['view', 'sell']
        }

        if required_role in permissions.get ( user_role, [] ):
            return True

        return False