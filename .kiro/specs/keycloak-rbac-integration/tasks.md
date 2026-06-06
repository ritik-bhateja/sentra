# Implementation Plan: Keycloak RBAC Integration

## Overview

This plan implements Keycloak as a dedicated RBAC (role) authority alongside the existing Google OAuth2 authentication. The implementation is ordered so foundational modules come first (role definitions, Keycloak client), then integration into the auth flow, then server-side enforcement, then frontend changes, and finally wiring/admin endpoints. Property-based tests validate each module immediately after implementation.

## Tasks

- [x] 1. Create role definitions module (`auth/roles.py`)
  - [x] 1.1 Implement the Role enum, DEFAULT_ROLE, ROLE_PRIORITY, and helper functions
    - Create `BackendAPI/auth/roles.py` with `Role(str, Enum)` defining `admin`, `viewer_with_query`, `viewer_without_query`
    - Implement `select_most_privileged(role_names)` that picks the highest-priority Sentra role from a list
    - Implement `coerce_role(value)` that validates a string into a Role or returns DEFAULT_ROLE
    - Implement `can_view_query(role)` returning True for admin and viewer_with_query
    - _Requirements: 2.1, 2.2, 2.3, 5.5, 6.2, 6.3, 10.1, 10.2_

  - [x] 1.2 Write property test for most-privileged role resolution
    - **Property 1: Most-privileged role resolution**
    - Use Hypothesis to generate arbitrary lists of role-name strings (including noise, duplicates, empty)
    - Assert `select_most_privileged` returns admin if present, else viewer_with_query if present, else DEFAULT_ROLE; result invariant under permutation
    - **Validates: Requirements 3.3, 5.2, 5.3, 5.5, 10.2**

  - [x] 1.3 Write property test for missing/invalid role claim defaulting
    - **Property 2: Missing or invalid role claim resolves to the default role**
    - Use Hypothesis to generate None, arbitrary non-Sentra strings, and valid role strings
    - Assert `coerce_role` returns DEFAULT_ROLE for invalid/missing inputs and the exact Role for valid inputs
    - **Validates: Requirements 6.3, 7.1, 7.4, 12.2**

- [x] 2. Create Keycloak client module (`auth/keycloak_client.py`)
  - [x] 2.1 Implement KeycloakClient class and resolve_role_for_email function
    - Create `BackendAPI/auth/keycloak_client.py` with `KeycloakClient` class reading env vars (KEYCLOAK_URL, KEYCLOAK_REALM, KEYCLOAK_CLIENT_ID, KEYCLOAK_CLIENT_SECRET, KEYCLOAK_ENABLED)
    - Implement `is_enabled()`, `_service_token()` (client credentials grant with caching), `get_realm_roles_for_email(email)`, `user_exists(email)`, `create_user(email)`, `assign_realm_role(user_id, role)`
    - Define `KeycloakUnavailable` exception class
    - Implement `resolve_role_for_email(email, client)` that returns DEFAULT_ROLE when disabled or on failure, otherwise calls `select_most_privileged`
    - _Requirements: 2.4, 2.5, 4.1, 5.1, 5.2, 5.3, 5.4, 12.4_

  - [x] 2.2 Write property test for disabled Keycloak always yields default role
    - **Property 10: Disabled Keycloak always yields the default role without a network call**
    - Use Hypothesis to generate arbitrary emails; set KEYCLOAK_ENABLED=False
    - Assert `resolve_role_for_email` returns DEFAULT_ROLE and performs no Keycloak request (via spy/mock)
    - **Validates: Requirements 12.4**

- [x] 3. Modify JWT handler to include role claim (`auth/jwt_handler.py`)
  - [x] 3.1 Add role parameter to create_token and preserve existing claims
    - Modify `BackendAPI/auth/jwt_handler.py` `create_token` to accept a `role` parameter (default `DEFAULT_ROLE.value`) and include it as a `role` claim in the JWT payload
    - Preserve existing `sub`, `email`, `exp`, `iat` claims unchanged
    - No changes to `verify_token` mechanics (role defaulting handled in middleware)
    - _Requirements: 6.1, 6.2, 6.4, 6.5_

  - [x] 3.2 Write property test for JWT role round-trip
    - **Property 3: JWT role round-trip preserves all claims**
    - Use Hypothesis to generate arbitrary user_id (positive int), email strings, and Role enum values
    - Assert decoded token has correct `sub`, `email`, `role`, and `exp > iat`; verification fails with wrong secret
    - **Validates: Requirements 6.1, 6.2, 6.4, 6.5**

- [x] 4. Modify auth middleware for role-aware context (`auth/middleware.py`)
  - [x] 4.1 Attach role from JWT claim to current user and add require_admin dependency
    - Modify `BackendAPI/auth/middleware.py` `get_current_user` to call `coerce_role(payload.get("role"))` and attach the result as `current_user.role`
    - Add `require_admin` dependency function that raises HTTPException(403) if `current_user.role != Role.ADMIN`
    - Import `Role`, `coerce_role` from `auth.roles`
    - _Requirements: 7.1, 7.3, 7.4, 9.2, 9.3, 9.4, 9.5_

  - [x] 4.2 Write property test for admin guard enforcement
    - **Property 9: Non-admin roles are denied admin operations**
    - Use Hypothesis (or parametrize over all Role values) to test `require_admin`
    - Assert HTTPException(403) for viewer_with_query and viewer_without_query; assert user returned for admin
    - **Validates: Requirements 9.2, 9.3, 9.5, 10.4**

- [x] 5. Create response filtering module (`auth/rbac.py`)
  - [x] 5.1 Implement filter_response_for_role and filter_messages_for_role
    - Create `BackendAPI/auth/rbac.py` with `filter_response_for_role(payload, role)` that strips `query_executed` for viewer_without_query
    - Implement `filter_messages_for_role(messages, role)` that applies the filter to message-format outputs (bot messages with dict content)
    - Both functions return copies, never mutate input
    - _Requirements: 8.1, 8.2, 8.3, 8.5, 10.3_

  - [x] 5.2 Write property test for query visibility filtering
    - **Property 4: Query visibility filtering by role**
    - Use Hypothesis to generate arbitrary dict payloads (with/without `query_executed`) and all Role values
    - Assert admin/viewer_with_query see full payload; viewer_without_query never sees `query_executed`; other fields preserved
    - **Validates: Requirements 8.1, 8.2, 8.3, 10.3**

  - [x] 5.3 Write property test for live vs stored response filtering equivalence
    - **Property 5: Live and stored responses are filtered identically**
    - Use Hypothesis to generate arbitrary assistant-response dicts and roles
    - Assert applying `filter_response_for_role` directly produces same query_executed visibility as going through `filter_messages_for_role` (the stored-history path)
    - **Validates: Requirements 8.5**

- [x] 6. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Create role sync service (`role_sync.py`)
  - [x] 7.1 Implement sync_users function and CLI interface
    - Create `BackendAPI/role_sync.py` with `sync_users(client, db)` that iterates RDS users, creates missing Keycloak users with DEFAULT_ROLE, skips existing ones, catches errors per-user
    - Return summary dict with `created`, `skipped`, `errors` counts
    - Add CLI entry point (`python role_sync.py sync`) following existing script conventions
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 12.1_

  - [x] 7.2 Write property test for sync coverage and default role assignment
    - **Property 6: Synchronization covers all RDS users and defaults new ones**
    - Use Hypothesis to generate arbitrary sets of emails with a subset pre-existing in FakeKeycloak
    - Assert after sync every email exists in Keycloak and newly created ones hold DEFAULT_ROLE
    - **Validates: Requirements 4.1, 4.4, 12.1**

  - [x] 7.3 Write property test for sync idempotency
    - **Property 7: Synchronization is idempotent for existing users**
    - Use Hypothesis with pre-existing Keycloak users carrying arbitrary roles
    - Assert running sync leaves existing users' roles unchanged and creates no duplicates
    - **Validates: Requirements 4.3**

  - [x] 7.4 Write property test for sync accounting accuracy
    - **Property 8: Synchronization accounting is exact**
    - Use Hypothesis to generate email sets with pre-existing subsets
    - Assert `created == |new emails|`, `skipped == |existing emails|`, and `created + skipped == total processed`
    - **Validates: Requirements 4.6**

- [x] 8. Set up local Keycloak development environment
  - [x] 8.1 Create docker-compose.keycloak.yml and realm export
    - Create `docker-compose.keycloak.yml` at project root with Keycloak 25.0 + Postgres 15-alpine services
    - Create `keycloak/realm-export.json` with pre-configured `sentra` realm, three realm roles, `sentra-backend` confidential client with service account
    - Add Keycloak env vars to `BackendAPI/.env.example` (KEYCLOAK_URL, KEYCLOAK_REALM, KEYCLOAK_CLIENT_ID, KEYCLOAK_CLIENT_SECRET, KEYCLOAK_ENABLED)
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6_

- [x] 9. Integrate role lookup into OAuth callback and wire endpoints (`Agent_Trigger.py`)
  - [x] 9.1 Modify /auth/google/callback to resolve role and pass to create_token
    - After RDS user validation and before token creation, call `resolve_role_for_email(user.email, keycloak_client)`
    - Pass `role.value` to `jwt_handler.create_token(user.id, user.email, role.value)`
    - Preserve all existing cookie attributes and redirect behavior unchanged
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 5.1, 5.2, 5.3, 5.4, 6.1_

  - [x] 9.2 Modify /query endpoint to filter response by role
    - After building `response_data`, apply `filter_response_for_role(response_data, current_user.role)` before returning
    - Store full unfiltered response in database (filtering is read-time only)
    - _Requirements: 8.1, 8.2, 8.3, 8.4_

  - [x] 9.3 Modify history read endpoints to filter stored responses by role
    - In `/api/sessions/{session_id}/turns` (message format): wrap output with `filter_messages_for_role(messages, current_user.role)`
    - In `/api/sessions/{session_id}/turns/raw`: filter each turn's `assistant_response` via `filter_response_for_role`
    - In `/api/sessions/{session_id}/messages`: apply same filter as /turns
    - _Requirements: 8.5_

  - [x] 9.4 Modify /auth/me to include role in response
    - Return `{**current_user.to_dict(), "role": current_user.role.value}` from the `/auth/me` endpoint
    - _Requirements: 7.2_

  - [x] 9.5 Add admin endpoints (/admin/users, /admin/keycloak/sync)
    - Add `GET /admin/users` protected by `Depends(require_admin)` that lists all authorized users
    - Add `POST /admin/keycloak/sync` protected by `Depends(require_admin)` that triggers `sync_users`
    - Non-admins receive HTTP 403 with descriptive message
    - _Requirements: 9.1, 9.2, 9.3, 9.4_

- [x] 10. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 11. Frontend role-aware rendering
  - [x] 11.1 Update AuthContext.jsx to expose role
    - Modify `Frontend/src/contexts/AuthContext.jsx` to expose `role` from the user data (returned by `/auth/me`)
    - Add `role: user?.role` to the AuthContext.Provider value
    - _Requirements: 11.1_

  - [x] 11.2 Modify ChatMessage.jsx to gate Query tab on role
    - Import `useAuth` and extract `role`
    - Define `canViewQuery = role === 'admin' || role === 'viewer_with_query'`
    - Replace all `content.query_executed &&` tab guards with `canViewQuery && content.query_executed &&`
    - Apply same guard to the active-tab query content body
    - _Requirements: 11.2, 11.3, 11.4, 11.5_

- [x] 12. Optional: Hook add_authorized_user.py to create Keycloak user on add
  - [x] 12.1 Add post-add hook to create Keycloak user with default role
    - After inserting a user into RDS, call `KeycloakClient.create_user(email)` + `assign_realm_role(uid, DEFAULT_ROLE)` if Keycloak is enabled
    - Gracefully handle Keycloak failures (log warning, don't block RDS add)
    - _Requirements: 3.4, 4.1, 4.4_

- [x] 13. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties (Properties 1–10 from design)
- The backend uses Python (FastAPI/Hypothesis); the frontend uses React (JSX)
- Keycloak is never on the sign-in path — Google OAuth remains the sole authentication mechanism
- All filtering is read-time only; stored data is never mutated
- The kill-switch (`KEYCLOAK_ENABLED=False`) degrades gracefully to the default role
