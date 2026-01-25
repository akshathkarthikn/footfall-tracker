"""
Database backup utilities.
"""

import os
import shutil
from datetime import datetime
from config import DATA_DIR, BACKUP_DIR


def create_backup() -> str:
    """
    Create a backup of the database.
    Returns the backup file path.
    """
    db_path = os.path.join(DATA_DIR, 'footfall.db')

    if not os.path.exists(db_path):
        raise FileNotFoundError("Database file not found")

    # Create backup filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_filename = f"footfall_{timestamp}.db"
    backup_path = os.path.join(BACKUP_DIR, backup_filename)

    # Ensure backup directory exists
    os.makedirs(BACKUP_DIR, exist_ok=True)

    # Copy database file
    shutil.copy2(db_path, backup_path)

    # Also copy the WAL and SHM files if they exist
    wal_path = db_path + "-wal"
    shm_path = db_path + "-shm"

    if os.path.exists(wal_path):
        shutil.copy2(wal_path, backup_path + "-wal")
    if os.path.exists(shm_path):
        shutil.copy2(shm_path, backup_path + "-shm")

    return backup_path


def list_backups() -> list:
    """
    List all available backups.
    Returns list of dicts with 'filename', 'path', 'size', 'created'.
    """
    if not os.path.exists(BACKUP_DIR):
        return []

    backups = []
    for filename in os.listdir(BACKUP_DIR):
        if filename.endswith('.db') and filename.startswith('footfall_'):
            path = os.path.join(BACKUP_DIR, filename)
            stat = os.stat(path)
            backups.append({
                'filename': filename,
                'path': path,
                'size': stat.st_size,
                'size_mb': round(stat.st_size / (1024 * 1024), 2),
                'created': datetime.fromtimestamp(stat.st_mtime)
            })

    # Sort by creation time, newest first
    backups.sort(key=lambda x: x['created'], reverse=True)
    return backups


def restore_backup(backup_path: str) -> bool:
    """
    Restore a backup to the main database.
    Warning: This will overwrite the current database!
    """
    db_path = os.path.join(DATA_DIR, 'footfall.db')

    if not os.path.exists(backup_path):
        raise FileNotFoundError("Backup file not found")

    # Copy backup to main database location
    shutil.copy2(backup_path, db_path)

    # Copy WAL and SHM files if they exist
    wal_backup = backup_path + "-wal"
    shm_backup = backup_path + "-shm"

    if os.path.exists(wal_backup):
        shutil.copy2(wal_backup, db_path + "-wal")
    if os.path.exists(shm_backup):
        shutil.copy2(shm_backup, db_path + "-shm")

    return True


def cleanup_old_backups(keep_count: int = 30):
    """
    Remove old backups, keeping only the most recent ones.
    """
    backups = list_backups()

    if len(backups) <= keep_count:
        return 0

    # Delete oldest backups
    deleted = 0
    for backup in backups[keep_count:]:
        try:
            os.remove(backup['path'])
            # Remove associated WAL/SHM files
            for ext in ['-wal', '-shm']:
                path = backup['path'] + ext
                if os.path.exists(path):
                    os.remove(path)
            deleted += 1
        except Exception:
            pass

    return deleted


def get_database_size() -> dict:
    """Get the current database size."""
    db_path = os.path.join(DATA_DIR, 'footfall.db')

    if not os.path.exists(db_path):
        return {'exists': False, 'size': 0, 'size_mb': 0}

    size = os.path.getsize(db_path)

    # Add WAL file size if exists
    wal_path = db_path + "-wal"
    if os.path.exists(wal_path):
        size += os.path.getsize(wal_path)

    return {
        'exists': True,
        'size': size,
        'size_mb': round(size / (1024 * 1024), 2)
    }


if __name__ == "__main__":
    # When run directly, create a backup
    import sys

    try:
        backup_path = create_backup()
        print(f"Backup created: {backup_path}")

        # Cleanup old backups
        deleted = cleanup_old_backups(keep_count=30)
        if deleted > 0:
            print(f"Cleaned up {deleted} old backups")

        sys.exit(0)
    except Exception as e:
        print(f"Backup failed: {e}")
        sys.exit(1)
