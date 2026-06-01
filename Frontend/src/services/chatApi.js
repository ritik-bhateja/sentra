/**
 * Chat API Service
 * Handles all API calls for chat history management
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

/**
 * Generic fetch wrapper with error handling
 */
async function apiFetch(endpoint, options = {}) {
  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error(`API Error [${endpoint}]:`, error);
    throw error;
  }
}

/**
 * Create a new chat session
 */
export async function createSession(sessionId, userId, title = 'New Chat') {
  return apiFetch('/api/sessions', {
    method: 'POST',
    body: JSON.stringify({
      session_id: sessionId,
      user_id: userId,
      title: title,
    }),
  });
}

/**
 * Get all sessions for a user
 */
export async function getUserSessions(userId) {
  return apiFetch(`/api/sessions/${userId}`);
}

/**
 * Get all messages for a session
 */
export async function getSessionMessages(sessionId) {
  return apiFetch(`/api/sessions/${sessionId}/messages`);
}

/**
 * Save a message to a session
 */
export async function saveMessage(messageId, sessionId, messageType, content, timestamp) {
  return apiFetch('/api/messages', {
    method: 'POST',
    body: JSON.stringify({
      message_id: messageId,
      session_id: sessionId,
      message_type: messageType,
      content: content,
      timestamp: timestamp,
    }),
  });
}

/**
 * Update session title
 */
export async function updateSessionTitle(sessionId, title) {
  return apiFetch(`/api/sessions/${sessionId}`, {
    method: 'PUT',
    body: JSON.stringify({
      title: title,
    }),
  });
}

/**
 * Delete a session
 */
export async function deleteSession(sessionId) {
  return apiFetch(`/api/sessions/${sessionId}`, {
    method: 'DELETE',
  });
}

/**
 * Send query to Bedrock Agent (existing endpoint)
 */
export async function sendQuery(userQuery, userId, sessionId, signal) {
  return apiFetch('/query', {
    method: 'POST',
    body: JSON.stringify({
      user_query: userQuery,
      user_id: userId,
      session_id: sessionId,
    }),
    signal: signal,
  });
}

/**
 * Migrate localStorage sessions to RDS
 */
export async function migrateLocalStorageToRDS(userId) {
  const sessionKey = `sentra_sessions_${userId}`;
  const localSessions = JSON.parse(localStorage.getItem(sessionKey) || '[]');
  
  if (localSessions.length === 0) {
    console.log('No local sessions to migrate');
    return { migrated: 0, failed: 0 };
  }

  console.log(`Migrating ${localSessions.length} sessions to RDS...`);
  
  let migrated = 0;
  let failed = 0;

  for (const session of localSessions) {
    try {
      // Create session in RDS
      await createSession(session.id, userId, session.title);
      
      // Save all messages
      if (session.messages && session.messages.length > 0) {
        for (const message of session.messages) {
          await saveMessage(
            message.id,
            session.id,
            message.type,
            message.content,
            message.timestamp
          );
        }
      }
      
      migrated++;
      console.log(`✅ Migrated session: ${session.title}`);
    } catch (error) {
      failed++;
      console.error(`❌ Failed to migrate session ${session.id}:`, error);
    }
  }

  // Clear localStorage after successful migration
  if (migrated > 0) {
    localStorage.removeItem(sessionKey);
    console.log(`✅ Migration complete: ${migrated} sessions migrated, ${failed} failed`);
  }

  return { migrated, failed };
}
