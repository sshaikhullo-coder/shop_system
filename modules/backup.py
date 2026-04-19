from database.db_manager import DatabaseManager
import os
import zipfile
import shutil
from datetime import datetime


class BackupManager:
    def __init__(self):
        self.db = DatabaseManager ()
        self.backup_dir = "backups"
        os.makedirs ( self.backup_dir, exist_ok=True )

    def create_backup(self):
        try:
            timestamp = datetime.now ().strftime ( '%Y%m%d_%H%M%S' )
            backup_file = os.path.join ( self.backup_dir, f"backup_{timestamp}.zip" )

            with zipfile.ZipFile ( backup_file, 'w', zipfile.ZIP_DEFLATED ) as zipf:
                if os.path.exists ( "shop_system.db" ):
                    zipf.write ( "shop_system.db", "shop_system.db" )

                if os.path.exists ( "reports" ):
                    for root, dirs, files in os.walk ( "reports" ):
                        for file in files:
                            file_path = os.path.join ( root, file )
                            zipf.write ( file_path, file_path )

            return True, backup_file
        except Exception as e:
            return False, str ( e )

    def restore_backup(self, backup_file):
        try:
            with zipfile.ZipFile ( backup_file, 'r' ) as zipf:
                zipf.extractall ( "restore_temp" )

            if os.path.exists ( "restore_temp/shop_system.db" ):
                shutil.copy2 ( "restore_temp/shop_system.db", "shop_system_restored.db" )

            shutil.rmtree ( "restore_temp" )
            return True, "База калыбына келтирилди"
        except Exception as e:
            return False, str ( e )