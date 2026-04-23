#!/bin/bash
set -euo pipefail

BACKUP_DIR="/var/backups/forenscope"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="forenscope_db"
DB_USER="forenscope"

mkdir -p "$BACKUP_DIR"

# Database backup
pg_dump -U "$DB_USER" "$DB_NAME" | gzip > "$BACKUP_DIR/db_${DATE}.sql.gz"

# Media backup
tar -czf "$BACKUP_DIR/media_${DATE}.tar.gz" -C /opt/forenscope media/

# Keep only last 30 days
find "$BACKUP_DIR" -name "*.gz" -mtime +30 -delete

echo "Backup completed: $DATE"
