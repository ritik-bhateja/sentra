-- ============================================
-- Sentra Chat History Database Schema V3
-- PRODUCTION-READY: UUID-based with conversation turns
-- ============================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================
-- Table 1: Chat Sessions
-- ============================================
CREATE TABLE IF NOT EXISTS chat_sessions (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(100) NOT NULL,  -- Email: harsh.kumar@sentra.com
    session_title VARCHAR(500),
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_activity_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    CONSTRAINT chk_session_status 
        CHECK (status IN ('ACTIVE', 'ARCHIVED', 'DELETED'))
);

-- Indexes for chat_sessions
CREATE INDEX IF NOT EXISTS idx_user_sessions 
    ON chat_sessions(user_id, last_activity_at DESC) 
    WHERE status = 'ACTIVE';

CREATE INDEX IF NOT EXISTS idx_session_status 
    ON chat_sessions(status, updated_at DESC);

-- ============================================
-- Table 2: Conversation Turns
-- ============================================
CREATE TABLE IF NOT EXISTS conversation_turns (
    turn_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL 
        REFERENCES chat_sessions(session_id) 
        ON DELETE CASCADE,
    turn_number INTEGER NOT NULL,
    user_query TEXT NOT NULL,
    assistant_response JSONB,  -- Store full response with type, data, explanation, etc.
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

-- Indexes for conversation_turns
CREATE INDEX IF NOT EXISTS idx_session_turns 
    ON conversation_turns(session_id, turn_number);

CREATE INDEX IF NOT EXISTS idx_turn_status 
    ON conversation_turns(status, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_assistant_response 
    ON conversation_turns USING GIN (assistant_response);

-- ============================================
-- Triggers
-- ============================================

-- Function to auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for chat_sessions.updated_at
DROP TRIGGER IF EXISTS trigger_update_session_timestamp ON chat_sessions;
CREATE TRIGGER trigger_update_session_timestamp
    BEFORE UPDATE ON chat_sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Function to auto-update last_activity_at when turn is added
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

-- Trigger to update session activity on new turn
DROP TRIGGER IF EXISTS trigger_update_session_activity ON conversation_turns;
CREATE TRIGGER trigger_update_session_activity
    AFTER INSERT ON conversation_turns
    FOR EACH ROW
    EXECUTE FUNCTION update_session_activity();

-- Function to auto-increment turn_number
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

-- Trigger to auto-set turn_number
DROP TRIGGER IF EXISTS trigger_set_turn_number ON conversation_turns;
CREATE TRIGGER trigger_set_turn_number
    BEFORE INSERT ON conversation_turns
    FOR EACH ROW
    EXECUTE FUNCTION set_turn_number();

-- ============================================
-- Helper Functions
-- ============================================

-- Function to get or create session
CREATE OR REPLACE FUNCTION get_or_create_session(
    p_user_id VARCHAR(100),
    p_session_title VARCHAR(500) DEFAULT 'New Chat'
)
RETURNS UUID AS $$
DECLARE
    v_session_id UUID;
BEGIN
    -- Try to get most recent active session
    SELECT session_id INTO v_session_id
    FROM chat_sessions
    WHERE user_id = p_user_id 
      AND status = 'ACTIVE'
    ORDER BY last_activity_at DESC
    LIMIT 1;
    
    -- If no active session, create new one
    IF v_session_id IS NULL THEN
        INSERT INTO chat_sessions (user_id, session_title)
        VALUES (p_user_id, p_session_title)
        RETURNING session_id INTO v_session_id;
    END IF;
    
    RETURN v_session_id;
END;
$$ LANGUAGE plpgsql;

-- Function to archive old sessions
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
-- Sample Queries
-- ============================================

-- Get user's active sessions
-- SELECT * FROM v_active_sessions WHERE user_id = 'harsh.kumar@sentra.com';

-- Get all turns for a session
-- SELECT * FROM conversation_turns WHERE session_id = 'xxx' ORDER BY turn_number;

-- Get latest turn in session
-- SELECT * FROM conversation_turns WHERE session_id = 'xxx' ORDER BY turn_number DESC LIMIT 1;

-- Archive sessions older than 30 days
-- SELECT archive_old_sessions(30);

-- Get session statistics
-- SELECT 
--     user_id,
--     COUNT(*) as total_sessions,
--     SUM(turn_count) as total_turns,
--     AVG(turn_count) as avg_turns_per_session
-- FROM v_active_sessions
-- GROUP BY user_id;

-- ============================================
-- Verification
-- ============================================

SELECT 'Schema V3 created successfully!' AS status;

-- Show table info
SELECT 
    table_name,
    (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name) as column_count
FROM information_schema.tables t
WHERE table_schema = 'public' 
  AND table_name IN ('chat_sessions', 'conversation_turns')
ORDER BY table_name;
