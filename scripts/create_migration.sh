#!/bin/bash
# Create a new migration

if [ -z "$1" ]; then
    echo "Usage: ./create_migration.sh <migration_message>"
    exit 1
fi

poetry run alembic revision --autogenerate -m "$1"

