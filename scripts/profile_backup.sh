#!/bin/bash
# Profile backup/restore script

if [ "$1" = "backup" ]; then
    echo "Creating profile backup..."
    tar -czf automation_profile_backup.tar.gz automation_profile/
    echo "Backup created: automation_profile_backup.tar.gz"
elif [ "$1" = "restore" ]; then
    echo "Restoring profile from backup..."
    tar -xzf automation_profile_backup.tar.gz
    echo "Profile restored from backup"
else
    echo "Usage: $0 [backup|restore]"
fi
