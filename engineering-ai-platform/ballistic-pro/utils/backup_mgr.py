import os
import shutil
from datetime import datetime

def run_backup(db_path="ballistics.db", backup_dir="backups", limit=5):
    """
    Realiza o backup do banco de dados SQLite e mantém apenas os 'limit' mais recentes.
    """
    if not os.path.exists(db_path):
        return None
    
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"ballistics_backup_{timestamp}.db"
    backup_path = os.path.join(backup_dir, backup_filename)
    
    try:
        shutil.copy2(db_path, backup_path)
        
        # Rotação de backups
        backups = sorted(
            [os.path.join(backup_dir, f) for f in os.listdir(backup_dir) if f.startswith("ballistics_backup_")],
            key=os.path.getctime
        )
        
        while len(backups) > limit:
            oldest = backups.pop(0)
            os.remove(oldest)
            
        return backup_path
    except Exception as e:
        print(f"[ERROR] Falha ao realizar backup: {e}")
        return None
