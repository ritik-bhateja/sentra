-- ============================================
-- Sentra Chat History Database Schema
-- Database: company_db (PostgreSQL)
-- ============================================

-- Table 1: Chat Sessions
CREATE TABLE IF NOT EXISTS chat_sessions (
    session_id VARCHAR(33) PRIMARY KEY,
    user_id VARCHAR(100) NOT NULL,
    title VARCHAR(255) DEFAULT 'New Chat',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index for fast user session lookup (most common query)
CREATE INDEX IF NOT EXISTS idx_user_sessions ON chat_sessions(user_id, updated_at DESC);

-- Table 2: Chat Messages
CREATE TABLE IF NOT EXISTS chat_messages (
    message_id VARCHAR(50) PRIMARY KEY,
    session_id VARCHAR(33) NOT NULL,
    message_type VARCHAR(10) NOT NULL CHECK (message_type IN ('user', 'bot')),
    content JSONB NOT NULL,
    timestamp BIGINT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_session FOREIGN KEY (session_id) 
        REFERENCES chat_sessions(session_id) 
        ON DELETE CASCADE
);

-- Index for fast message retrieval by session
CREATE INDEX IF NOT EXISTS idx_session_messages ON chat_messages(session_id, timestamp);

-- Index for JSONB content queries (for future analytics)
CREATE INDEX IF NOT EXISTS idx_message_content ON chat_messages USING GIN (content);

-- Trigger function for auto-updating updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-update updated_at on sessions
DROP TRIGGER IF EXISTS update_chat_sessions_updated_at ON chat_sessions;
CREATE TRIGGER update_chat_sessions_updated_at
    BEFORE UPDATE ON chat_sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Verify tables created
SELECT 'Schema created successfully!' AS status;
