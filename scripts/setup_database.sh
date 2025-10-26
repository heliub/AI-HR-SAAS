#!/bin/bash

# AI HR SaaS Database Setup Script
# This script creates database schema and imports mock data
# Usage: ./scripts/setup_database.sh [--reset]

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Database configuration
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-55000}"
DB_USER="${DB_USER:-postgres}"
DB_PASSWORD="${DB_PASSWORD:-postgrespw}"
DB_NAME="${DB_NAME:-postgres}"

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}AI HR SaaS Database Setup${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${YELLOW}Database Configuration:${NC}"
echo "  Host: $DB_HOST"
echo "  Port: $DB_PORT"
echo "  User: $DB_USER"
echo "  Database: $DB_NAME"
echo ""

# Check if reset flag is provided
RESET_DB=false
if [ "$1" == "--reset" ]; then
    RESET_DB=true
    echo -e "${YELLOW}⚠️  Reset mode enabled - This will drop all existing data!${NC}"
    read -p "Are you sure you want to continue? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        echo -e "${RED}❌ Operation cancelled${NC}"
        exit 1
    fi
    echo ""
fi

# Function to execute SQL file
execute_sql_file() {
    local sql_file=$1
    local description=$2
    
    echo -e "${BLUE}▶ $description...${NC}"
    
    if [ ! -f "$sql_file" ]; then
        echo -e "${RED}❌ SQL file not found: $sql_file${NC}"
        exit 1
    fi
    
    PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f "$sql_file" > /dev/null 2>&1
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ $description completed${NC}"
    else
        echo -e "${RED}❌ $description failed${NC}"
        exit 1
    fi
}

# Function to execute SQL command
execute_sql() {
    local sql_cmd=$1
    local description=$2
    
    echo -e "${BLUE}▶ $description...${NC}"
    
    PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "$sql_cmd" > /dev/null 2>&1
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ $description completed${NC}"
    else
        echo -e "${RED}❌ $description failed${NC}"
        exit 1
    fi
}

# Test database connection
echo -e "${BLUE}▶ Testing database connection...${NC}"
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SELECT version();" > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Database connection successful${NC}"
    echo ""
else
    echo -e "${RED}❌ Database connection failed${NC}"
    echo -e "${YELLOW}Please check your database configuration:${NC}"
    echo "  - Is PostgreSQL running?"
    echo "  - Are the connection parameters correct?"
    echo "  - DB: postgres://postgres:postgrespw@localhost:55000"
    exit 1
fi

# Step 1: Drop existing tables if reset mode
if [ "$RESET_DB" = true ]; then
    echo -e "${YELLOW}Step 1: Dropping existing tables...${NC}"
    
    DROP_TABLES_SQL="
    DROP TABLE IF EXISTS 
      chat_messages, chat_sessions, candidate_chat_history, 
      interviews, recruitment_tasks, ai_match_results, 
      job_preferences, education_histories, project_experiences, work_experiences,
      resumes, job_channels, channels, jobs, 
      auth_tokens, user_settings, users, activity_logs, email_logs, tenants 
    CASCADE;
    "
    
    execute_sql "$DROP_TABLES_SQL" "Dropping existing tables"
    echo ""
fi

# Step 2: Create database schema
echo -e "${YELLOW}Step 2: Creating database schema...${NC}"
execute_sql_file "$PROJECT_ROOT/docs/DATABASE_SCHEMA.sql" "Creating tables and indexes"
echo ""

# Step 3: Import mock data
echo -e "${YELLOW}Step 3: Importing mock data...${NC}"
execute_sql_file "$PROJECT_ROOT/scripts/import_mock_data.sql" "Importing initial data"
echo ""

# Step 4: Verify data
echo -e "${YELLOW}Step 4: Verifying imported data...${NC}"
echo -e "${BLUE}▶ Counting records...${NC}"

VERIFY_SQL="
SELECT 
  (SELECT COUNT(*) FROM tenants) AS tenants,
  (SELECT COUNT(*) FROM users) AS users,
  (SELECT COUNT(*) FROM jobs) AS jobs,
  (SELECT COUNT(*) FROM channels) AS channels,
  (SELECT COUNT(*) FROM resumes) AS resumes,
  (SELECT COUNT(*) FROM interviews) AS interviews,
  (SELECT COUNT(*) FROM chat_sessions) AS chat_sessions;
"

PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "$VERIFY_SQL"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✓ Database setup completed successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}Summary:${NC}"
echo "  • Database schema created"
echo "  • Mock data imported"
echo "  • Tables verified"
echo ""
echo -e "${BLUE}You can now start the application:${NC}"
echo "  uvicorn app.main:app --reload"
echo ""
echo -e "${BLUE}Or run migrations:${NC}"
echo "  ./scripts/migrate.sh"
echo ""

