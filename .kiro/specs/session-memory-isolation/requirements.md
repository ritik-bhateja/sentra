# Requirements Document

## Introduction

The Sentra AI chatbot system currently shares conversation memory across all users and all chat sessions due to hardcoded actor and session identifiers in the backend. This feature will implement proper session and user isolation for the conversation memory system, ensuring that each user's chat sessions maintain independent conversation contexts. The system uses AWS Bedrock AgentCore Memory with a Strands Agent framework, and the frontend already manages unique session IDs per chat in localStorage.

## Glossary

- **Actor ID**: A unique identifier representing a user in the memory system (e.g., "kamaljeet.singh", "vishal.saxena")
- **Session ID**: A unique identifier representing a specific chat conversation (e.g., timestamp-based ID like "1734012345678")
- **Memory Client**: AWS Bedrock AgentCore Memory service that stores and retrieves conversation history
- **Conversation Context**: The historical messages loaded from memory when initializing an agent
- **Frontend**: React-based user interface that manages chat sessions in localStorage
- **Backend**: Python Flask API and Bedrock AgentCore runtime that processes queries
- **SQLQueryExecutor**: The agent class that initializes the Strands Agent with memory hooks
- **Memory Hook**: Event handlers that load and save conversation history during agent lifecycle

## Requirements

### Requirement 1

**User Story:** As a system user, I want my conversation history to be isolated from other users, so that I only see my own previous messages and not messages from other users.

#### Acceptance Criteria

1. WHEN a user sends a query THEN the system SHALL use the user's unique identifier as the actor_id for memory operations
2. WHEN the agent loads conversation history THEN the system SHALL retrieve only messages associated with the current user's actor_id
3. WHEN a user logs in with a different user_id THEN the system SHALL NOT display conversation history from other users
4. WHEN storing a new message THEN the system SHALL associate the message with the current user's actor_id

### Requirement 2

**User Story:** As a user, I want each of my chat sessions to maintain separate conversation contexts, so that starting a new chat gives me a fresh conversation without previous chat history.

#### Acceptance Criteria

1. WHEN a user creates a new chat session THEN the system SHALL generate a unique session_id for that chat
2. WHEN the agent loads conversation history THEN the system SHALL retrieve only messages associated with the current session_id
3. WHEN a user switches between existing chat sessions THEN the system SHALL load the conversation history specific to the selected session_id
4. WHEN storing a new message THEN the system SHALL associate the message with the current session_id
5. WHEN a user returns to a previous chat session THEN the system SHALL display the conversation history from that specific session

### Requirement 3

**User Story:** As a developer, I want the frontend session identifiers to be passed through to the backend memory system, so that the existing frontend session management integrates with backend memory isolation.

#### Acceptance Criteria

1. WHEN the frontend sends a query request THEN the system SHALL include both user_id and session_id in the request payload
2. WHEN the Flask API receives a request THEN the system SHALL extract both user_id and session_id from the payload
3. WHEN the Flask API invokes the AgentCore runtime THEN the system SHALL pass both user_id and session_id in the invocation payload
4. WHEN the AgentCore entrypoint initializes the SQLQueryExecutor THEN the system SHALL pass the received user_id as actor_id and session_id as session_id parameters

### Requirement 4

**User Story:** As a system administrator, I want the memory system to validate required identifiers and return clear errors, so that API consumers understand when mandatory parameters are missing.

#### Acceptance Criteria

1. WHEN a request arrives without a user_id THEN the system SHALL return an API error indicating missing actor_id
2. WHEN a request arrives without a session_id THEN the system SHALL return an API error indicating missing session_id
3. WHEN memory operations fail due to invalid identifiers THEN the system SHALL log the error and return an appropriate error response
4. WHEN the agent cannot load conversation history due to memory errors THEN the system SHALL log the error and initialize with an empty conversation context

### Requirement 5

**User Story:** As a user, I want my conversation memory to persist across page refreshes within the same chat session, so that I can continue conversations seamlessly.

#### Acceptance Criteria

1. WHEN a user refreshes the browser page THEN the system SHALL maintain the same session_id for the active chat
2. WHEN the agent initializes after a page refresh THEN the system SHALL load the conversation history using the persisted session_id
3. WHEN a user sends a message after a page refresh THEN the system SHALL continue storing messages in the same session_id

### Requirement 6

**User Story:** As a developer, I want to validate that memory isolation is working correctly, so that I can verify different users and sessions have independent conversation contexts.

#### Acceptance Criteria

1. WHEN testing with multiple users THEN the system SHALL demonstrate that each user's memory is isolated
2. WHEN testing with multiple sessions for the same user THEN the system SHALL demonstrate that each session's memory is isolated
3. WHEN querying the memory store THEN the system SHALL show messages grouped by actor_id and session_id
4. WHEN switching between sessions THEN the system SHALL load different conversation histories for different session_ids
