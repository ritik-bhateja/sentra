# Implementation Plan

- [x] 1. Update Frontend to send session_id in API requests
  - Modify `ChatInterface.jsx` handleSubmit function to include currentSessionId in request payload
  - Ensure session_id is sent alongside user_query and user_id
  - _Requirements: 3.1_

- [x] 2. Update Flask API to validate and forward session identifiers
  - Extract session_id from incoming request payload in Agent_Trigger.py
  - Add validation to check for presence of user_id (return 400 error if missing)
  - Add validation to check for presence of session_id (return 400 error if missing)
  - Include session_id in the AgentCore invocation payload
  - _Requirements: 3.2, 4.1, 4.2_

-       [x] 3. Update AgentCore entrypoint to use dynamic identifiers
  - Modify main.py to extract user_id and session_id from payload
  - Add validation for both identifiers (return error response if missing)
  - Pass user_id as actor_id parameter to SQLQueryExecutor
  - Pass session_id as session_id parameter to SQLQueryExecutor
  - Remove hardcoded "harsh_kumar" and "sentra_session" values
  - _Requirements: 3.3, 3.4, 4.1, 4.2_

- [x] 4. Final Checkpoint - Verify identifier flow works end-to-end
  - Ensure all tests pass, ask the user if questions arise.
