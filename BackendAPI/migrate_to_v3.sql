-- ============================================
-- Migration Script: V2 → V3
-- CAUTION: This will DROP existing tables!
-- Backup your data before running this script
-- ============================================

-- Step 1: Backup existing data (optional - uncomment if needed)
-- CREATE TABLE chat_sessions_backup AS SELECT * FROM chat_sessions;
-- CREATE TABLE chat_messages_backup AS SELECT * FROM chat_messages;

-- Step 2: Drop existing tables and related objects
DROP TRIGGER IF EXISTS trigger_update_session_timestamp ON chat_sessions CASCADE;
DROP TRIGGER IF EXISTS trigger_update_session_activity ON conversation_turns CASCADE;
DROP TRIGGER IF EXISTS trigger_set_turn_number ON conversation_turns CASCADE;

DROP VIEW IF EXISTS v_active_sessions CASCADE;
DROP VIEW IF EXISTS v_session_conversations CASCADE;
DROP TABLE IF EXISTS conversation_turns CASCADE;
DROP TABLE IF EXISTS chat_sessions CASCADE;

DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE;
DROP FUNCTION IF EXISTS update_session_activity() CASCADE;
DROP FUNCTION IF EXISTS set_turn_number() CASCADE;
DROP FUNCTION IF EXISTS set_message_sequence_number() CASCADE;
DROP FUNCTION IF EXISTS get_or_create_session(VARCHAR, VARCHAR) CASCADE;
DROP FUNCTION IF EXISTS archive_old_sessions(INTEGER) CASCADE;

-- Step 3: Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Step 4: Create V3 schema
-- (The rest of the schema from database_schema_v3.sql follows)

-- ============================================
-- Table 1: Chat Sessions
-- ============================================
CREATE TABLE chat_sessions (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(100) NOT NULL,
    session_title VARCHAR(500),
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_activity_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    CONSTRAINT chk_session_status 
        CHECK (status IN ('ACTIVE', 'ARCHIVED', 'DELETED'))
);

CREATE INDEX idx_user_sessions 
    ON chat_sessions(user_id, last_activity_at DESC) 
    WHERE status = 'ACTIVE';

CREATE INDEX idx_session_status 
    ON chat_sessions(status, updated_at DESC);

-- ============================================
-- Table 2: Conversation Turns
-- ============================================
CREATE TABLE conversation_turns (
    turn_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL 
        REFERENCES chat_sessions(session_id) 
        ON DELETE CASCADE,
    turn_number INTEGER NOT NULL,
    user_query TEXT NOT NULL,
    assistant_response JSONB,
    model_name VARCHAR(100) DEFAULT 'moonshotai.kimi-k2.5',
    status VARCHAR(20) NOT NULL DEFAULT 'COMPLETED',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    error_message TEXT,
    
    CONSTRAINT chk_turn_status 
        CHECK (status IN ('PENDING', 'RUNNING', 'COMPLETED', 'FAILED')),
    CONSTRAINT uq_session_turn 
        UNIQUE (session_id, turn_number)
);

CREATE INDEX idx_session_turns 
    ON conversation_turns(session_id, turn_number);

CREATE INDEX idx_turn_status 
    ON conversation_turns(status, created_at DESC);

CREATE INDEX idx_assistant_response 
    ON conversation_turns USING GIN (assistant_response);

-- ============================================
-- Triggers
-- ============================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_session_timestamp
    BEFORE UPDATE ON chat_sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE OR REPLACE FUNCTION update_session_activity()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE chat_sessions 
    SET last_activity_at = NOW(),
        updated_at = NOW()
    WHERE session_id = NEW.session_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_session_activity
    AFTER INSERT ON conversation_turns
    FOR EACH ROW
    EXECUTE FUNCTION update_session_activity();

CREATE OR REPLACE FUNCTION set_turn_number()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.turn_number IS NULL THEN
        SELECT COALESCE(MAX(turn_number), 0) + 1
        INTO NEW.turn_number
        FROM conversation_turns
        WHERE session_id = NEW.session_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_set_turn_number
    BEFORE INSERT ON conversation_turns
    FOR EACH ROW
    EXECUTE FUNCTION set_turn_number();

-- ============================================
-- Helper Functions
-- ============================================

CREATE OR REPLACE FUNCTION get_or_create_session(
    p_user_id VARCHAR(100),
    p_session_title VARCHAR(500) DEFAULT 'New Chat'
)
RETURNS UUID AS $$
DECLARE
    v_session_id UUID;
BEGIN
    SELECT session_id INTO v_session_id
    FROM chat_sessions
    WHERE user_id = p_user_id 
      AND status = 'ACTIVE'
    ORDER BY last_activity_at DESC
    LIMIT 1;
    
    IF v_session_id IS NULL THEN
        INSERT INTO chat_sessions (user_id, session_title)
        VALUES (p_user_id, p_session_title)
        RETURNING session_id INTO v_session_id;
    END IF;
    
    RETURN v_session_id;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION archive_old_sessions(days_old INTEGER DEFAULT 30)
RETURNS INTEGER AS $$
DECLARE
    archived_count INTEGER;
BEGIN
    UPDATE chat_sessions
    SET status = 'ARCHIVED',
        updated_at = NOW()
    WHERE status = 'ACTIVE'
      AND last_activity_at < NOW() - (days_old || ' days')::INTERVAL;
    
    GET DIAGNOSTICS archived_count = ROW_COUNT;
    RETURN archived_count;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- Verification
-- ============================================

SELECT '✅ Migration to V3 completed successfully!' AS status;

-- Show created objects
SELECT 'Tables:' as object_type, table_name as name
FROM information_schema.tables
WHERE table_schema = 'public' 
  AND table_name IN ('chat_sessions', 'conversation_turns')
UNION ALL
SELECT 'Functions:', routine_name
FROM information_schema.routines
WHERE routine_schema = 'public'
  AND routine_type = 'FUNCTION'
  AND routine_name IN ('update_updated_at_column', 'update_session_activity', 'set_turn_number', 'get_or_create_session', 'archive_old_sessions')
ORDER BY object_type, name;
