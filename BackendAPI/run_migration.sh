#!/bin/bash

# ============================================
# Migration Script Runner
# Migrates from V2 to V3 schema
# ============================================

# Configuration
DB_HOST="database-2-instance-1.crwu46wug6kx.ap-south-1.rds.amazonaws.com"
DB_PORT="5432"
DB_NAME="company_db"
DB_USER="postgres"

echo "============================================"
echo "Sentra Chat System - V3 Migration"
echo "============================================"
echo ""
echo "⚠️  WARNING: This will DROP existing tables!"
echo "   - chat_sessions"
echo "   - chat_messages"
echo "   - conversation_turns"
echo ""
read -p "Do you want to continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "❌ Migration cancelled"
    exit 1
fi

echo ""
echo "📦 Running migration..."
echo ""

psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f migrate_to_v3.sql

if [ $? -eq 0 ]; then
    echo ""
    echo "============================================"
    echo "✅ Migration completed successfully!"
    echo "============================================"
    echo ""
    echo "Next steps:"
    echo "1. Update code: cp models_v3.py models.py"
    echo "2. Update API: cp Agent_Trigger_v3.py Agent_Trigger.py"
    echo "3. Start server: python3 Agent_Trigger.py"
    echo ""
else
    echo ""
    echo "============================================"
    echo "❌ Migration failed!"
    echo "============================================"
    echo ""
    echo "Check the error messages above."
    echo "Your data has NOT been modified."
    exit 1
fi
