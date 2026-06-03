-- ============================================
-- Sentra Chat History Database Schema V2
-- IMPROVED: Better message sequencing
-- ============================================

-- Table 1: Chat Sessions (unchanged)
CREATE TABLE IF NOT EXISTS chat_sessions (
    session_id VARCHAR(33) PRIMARY KEY,
    user_id VARCHAR(100) NOT NULL,
    title VARCHAR(255) DEFAULT 'New Chat',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_user_sessions ON chat_sessions(user_id, updated_at DESC);

-- Table 2: Chat Messages (IMPROVED)
CREATE TABLE IF NOT EXISTS chat_messages (
    -- Primary key: Auto-incrementing ID for guaranteed uniqueness
    id BIGSERIAL PRIMARY KEY,
    
    -- Message identification
    message_id VARCHAR(50) NOT NULL UNIQUE,  -- Frontend-generated ID (kept for compatibility)
    session_id VARCHAR(33) NOT NULL,
    
    -- Sequence number within session (auto-incremented per session)
    sequence_number INTEGER NOT NULL,
    
    -- Message data
    message_type VARCHAR(10) NOT NULL CHECK (message_type IN ('user', 'bot')),
    content JSONB NOT NULL,  -- Flexible: can store string or object
    
    -- Timing
    timestamp BIGINT NOT NULL,  -- Frontend timestamp (milliseconds)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign key
    CONSTRAINT fk_session FOREIGN KEY (session_id) 
        REFERENCES chat_sessions(session_id) 
        ON DELETE CASCADE,
    
    -- Unique constraint: sequence_number must be unique per session
    CONSTRAINT unique_session_sequence UNIQUE (session_id, sequence_number)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_session_messages ON chat_messages(session_id, sequence_number);
CREATE INDEX IF NOT EXISTS idx_session_timestamp ON chat_messages(session_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_message_content ON chat_messages USING GIN (content);

-- Function to auto-increment sequence_number per session
CREATE OR REPLACE FUNCTION set_message_sequence_number()
RETURNS TRIGGER AS $$
BEGIN
    -- Get the next sequence number for this session
    SELECT COALESCE(MAX(sequence_number), 0) + 1
    INTO NEW.sequence_number
    FROM chat_messages
    WHERE session_id = NEW.session_id;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-set sequence_number
DROP TRIGGER IF EXISTS trigger_set_message_sequence ON chat_messages;
CREATE TRIGGER trigger_set_message_sequence
    BEFORE INSERT ON chat_messages
    FOR EACH ROW
    WHEN (NEW.sequence_number IS NULL)
    EXECUTE FUNCTION set_message_sequence_number();

-- Trigger for auto-updating updated_at on sessions
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_chat_sessions_updated_at ON chat_sessions;
CREATE TRIGGER update_chat_sessions_updated_at
    BEFORE UPDATE ON chat_sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- View for easy message retrieval with sequence
CREATE OR REPLACE VIEW v_session_messages AS
SELECT 
    m.id,
    m.message_id,
    m.session_id,
    m.sequence_number,
    m.message_type,
    m.content,
    m.timestamp,
    m.created_at,
    s.user_id,
    s.title as session_title
FROM chat_messages m
JOIN chat_sessions s ON m.session_id = s.session_id
ORDER BY m.session_id, m.sequence_number;

-- Verify schema
SELECT 'Schema V2 created successfully!' AS status;

-- Example queries:
-- Get messages in correct order:
-- SELECT * FROM chat_messages WHERE session_id = 'xxx' ORDER BY sequence_number;
--
-- Get latest message in session:
-- SELECT * FROM chat_messages WHERE session_id = 'xxx' ORDER BY sequence_number DESC LIMIT 1;
--
-- Count messages in session:
-- SELECT COUNT(*) FROM chat_messages WHERE session_id = 'xxx';
