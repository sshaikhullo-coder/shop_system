class UserManager:
    def __init__(self, db_manager):
        self.db_manager = db_manager

    def get_all_users(self):
        """Бардык колдонуучуларды алуу"""
        conn = self.db_manager.get_connection ()
        cursor = conn.cursor ()

        cursor.execute ( 'SELECT id, username, role, full_name, email, created_at FROM users' )
        users = cursor.fetchall ()
        conn.close ()

        return [{
            'id': u[0],
            'username': u[1],
            'role': u[2],
            'full_name': u[3],
            'email': u[4],
            'created_at': u[5]
        } for u in users]

    def add_user(self, username, password, role, full_name, email):
        """Жаңы колдонуучу кошуу"""
        conn = self.db_manager.get_connection ()
        cursor = conn.cursor ()

        try:
            cursor.execute ( '''
                INSERT INTO users (username, password, role, full_name, email)
                VALUES (?, ?, ?, ?, ?)
            ''', (username, password, role, full_name, email) )
            conn.commit ()
            return True
        except Exception as e:
            print ( f"Ката: {e}" )
            return False
        finally:
            conn.close ()

    def delete_user(self, user_id):
        """Колдонуучуну өчүрүү"""
        conn = self.db_manager.get_connection ()
        cursor = conn.cursor ()

        cursor.execute ( 'DELETE FROM users WHERE id = ?', (user_id,) )
        conn.commit ()
        conn.close ()
        return True

    def update_user(self, user_id, full_name=None, email=None):
        """Колдонуучунун маалыматын жаңыртуу"""
        conn = self.db_manager.get_connection ()
        cursor = conn.cursor ()

        if full_name:
            cursor.execute ( 'UPDATE users SET full_name = ? WHERE id = ?', (full_name, user_id) )
        if email:
            cursor.execute ( 'UPDATE users SET email = ? WHERE id = ?', (email, user_id) )

        conn.commit ()
        conn.close ()
        return True