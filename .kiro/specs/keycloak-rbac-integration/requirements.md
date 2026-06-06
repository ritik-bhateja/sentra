# Requirements Document

## Introduction

This feature introduces **Keycloak as a dedicated Role-Based Access Control (RBAC) authority** for the Sentra Banking & Insurance AI Chatbot. Keycloak is used **only** to determine each user's role; it is **not** used for authentication. Google OAuth2 remains the sole authentication mechanism, and the existing application JWT (stored in the HTTP-only `sentra_jwt_token` cookie) continues to be the session credential.

The RDS `users` table remains the source of truth for **which users are authorized to log in** and intentionally stays role-free. Keycloak becomes the source of truth for **what role each authorized user holds**. Authorized users are mirrored from RDS into Keycloak so that a role can be assigned to each one.

During the existing Google OAuth callback, after a user is validated against RDS, the backend looks up the user's role in Keycloak and embeds that role as a claim in the application JWT. No second login is introduced. Three roles are supported: a full-access **Admin** role and two viewer roles that differ only in whether the executed SQL query is visible. Role enforcement occurs on the server (authoritative) and is mirrored in the frontend (user experience).

This feature explicitly does **not** reintroduce the deprecated CIF_NO-based banking RBAC concept; banking columns are no longer in use. RBAC here is strictly about (a) Admin versus Viewer capabilities and (b) visibility of the executed SQL query.

## Glossary

- **Sentra_System**: The complete Sentra Banking & Insurance AI Chatbot application, including backend API, frontend, and supporting services.
- **Backend_API**: The FastAPI service defined in `BackendAPI/Agent_Trigger.py` that exposes authentication, query, and session endpoints.
- **OAuth_Callback_Handler**: The `/auth/google/callback` endpoint logic in `BackendAPI/Agent_Trigger.py` that validates the user against RDS and issues the application JWT.
- **JWT_Handler**: The component in `BackendAPI/auth/jwt_handler.py` that creates and verifies the application JWT.
- **Auth_Middleware**: The `get_current_user` dependency in `BackendAPI/auth/middleware.py` that validates the JWT and resolves the current user.
- **Keycloak**: The external Keycloak server acting solely as the role authority for Sentra.
- **Sentra_Realm**: The Keycloak realm dedicated to Sentra that contains Sentra users and roles.
- **Role_Sync_Service**: The backend component or script that mirrors authorized users from the RDS `users` table into the Sentra_Realm in Keycloak.
- **Keycloak_Client**: The backend module that communicates with Keycloak over the Keycloak Admin REST API to read user roles and manage user records.
- **RDS_Users_Table**: The PostgreSQL `users` table (`BackendAPI/models_v3.py`, `User` model) that lists authorized login emails and remains role-free.
- **Query_Endpoint**: The `/query` endpoint in `BackendAPI/Agent_Trigger.py` that returns agent responses, including the `query_executed` field.
- **Query_Executed_Field**: The `query_executed` field in a `/query` response that contains the executed SQL statement.
- **ChatMessage_Component**: The frontend component `Frontend/src/components/ChatMessage.jsx` that renders message content, including the SQL "Query" tab.
- **Auth_Context**: The frontend authentication state provider `Frontend/src/contexts/AuthContext.jsx`.
- **Role**: A named authorization level assigned to a user. Permitted values are `admin`, `viewer_with_query`, and `viewer_without_query`.
- **Admin_Role**: The `admin` role, which grants full access to all capabilities and data fields.
- **Viewer_With_Query_Role**: The `viewer_with_query` role, a non-admin role permitted to view the Query_Executed_Field.
- **Viewer_Without_Query_Role**: The `viewer_without_query` role, a non-admin role not permitted to view the Query_Executed_Field. This is the most restrictive role.
- **Default_Role**: The role assigned when no explicit role is found for a user in Keycloak; equal to `viewer_without_query`.
- **Role_Claim**: The JWT claim named `role` that carries the user's Role value.
- **Authorized_User**: A user whose email exists in the RDS_Users_Table and is therefore permitted to log in.

## Requirements

### Requirement 1: Preserve Existing Google OAuth2 Authentication

**User Story:** As an existing Sentra user, I want my Google sign-in experience to remain unchanged, so that adding RBAC does not disrupt how I log in.

#### Acceptance Criteria

1. THE Sentra_System SHALL use Google OAuth2 as the only authentication mechanism.
2. THE OAuth_Callback_Handler SHALL continue to issue the application JWT in the existing HTTP-only cookie named `sentra_jwt_token`.
3. THE Sentra_System SHALL authenticate users without requiring any sign-in interaction with Keycloak.
4. WHEN an Authorized_User completes Google OAuth sign-in, THE OAuth_Callback_Handler SHALL redirect the user to the frontend application using the existing redirect behavior.
5. IF the user's email is absent from the RDS_Users_Table, THEN THE OAuth_Callback_Handler SHALL deny access using the existing `access_denied` redirect behavior.
6. THE Sentra_System SHALL preserve the existing JWT cookie attributes for `httponly`, `secure`, `samesite`, `max_age`, `domain`, and `path`.

### Requirement 2: Configure Keycloak Realm and Roles

**User Story:** As a system administrator, I want a dedicated Keycloak realm with the three Sentra roles defined, so that roles can be assigned to users from a single authority.

#### Acceptance Criteria

1. THE Sentra_Realm SHALL define the role `admin`.
2. THE Sentra_Realm SHALL define the role `viewer_with_query`.
3. THE Sentra_Realm SHALL define the role `viewer_without_query`.
4. THE Keycloak_Client SHALL authenticate to Keycloak using credentials supplied through environment variables.
5. WHERE Keycloak connection settings are required, THE Backend_API SHALL read the Keycloak server URL, realm name, client identifier, and client secret from environment variables.
6. THE Sentra_Realm SHALL serve as the sole authority for the Role value of each user.

### Requirement 3: Keep RDS Role-Free as the Login Authority

**User Story:** As a system administrator, I want RDS to remain the authority for who may log in without storing roles, so that role management stays centralized in Keycloak.

#### Acceptance Criteria

1. THE RDS_Users_Table SHALL remain the authority for which emails are authorized to log in.
2. THE RDS_Users_Table SHALL contain no column that stores a Role value.
3. THE Sentra_System SHALL determine each user's Role exclusively from Keycloak.
4. WHEN an email is added to or removed from the RDS_Users_Table, THE Sentra_System SHALL treat that change as the authoritative change to login authorization.

### Requirement 4: Synchronize Authorized Users from RDS into Keycloak

**User Story:** As a system administrator, I want authorized RDS users mirrored into Keycloak, so that each login-authorized user has a corresponding Keycloak record that can hold a role.

#### Acceptance Criteria

1. WHEN the Role_Sync_Service runs, THE Role_Sync_Service SHALL create a Keycloak user in the Sentra_Realm for each Authorized_User whose email has no matching Keycloak user.
2. THE Role_Sync_Service SHALL match an RDS user to a Keycloak user by email.
3. IF a Keycloak user already exists for an Authorized_User email, THEN THE Role_Sync_Service SHALL leave that Keycloak user's existing Role assignment unchanged.
4. WHEN the Role_Sync_Service creates a new Keycloak user, THE Role_Sync_Service SHALL assign the Default_Role to that user.
5. IF the Role_Sync_Service cannot reach Keycloak, THEN THE Role_Sync_Service SHALL report a descriptive error identifying the synchronization failure.
6. THE Role_Sync_Service SHALL record a summary of the count of users created and the count of users skipped during each synchronization run.

### Requirement 5: Look Up User Role During the Google OAuth Callback

**User Story:** As an authenticated user, I want my role determined at login time, so that my permissions are established for my session without an extra login step.

#### Acceptance Criteria

1. WHEN an Authorized_User is validated against the RDS_Users_Table during the OAuth callback, THE OAuth_Callback_Handler SHALL request the user's Role from Keycloak using the user's email.
2. WHEN Keycloak returns a single Sentra role for the user, THE OAuth_Callback_Handler SHALL use that role as the user's Role.
3. IF Keycloak returns no Sentra role for the user, THEN THE OAuth_Callback_Handler SHALL set the user's Role to the Default_Role.
4. IF the OAuth_Callback_Handler cannot reach Keycloak during role lookup, THEN THE OAuth_Callback_Handler SHALL set the user's Role to the Default_Role and SHALL record the lookup failure.
5. WHEN Keycloak returns more than one Sentra role for the user, THE OAuth_Callback_Handler SHALL select the most privileged role in the order `admin`, then `viewer_with_query`, then `viewer_without_query`.

### Requirement 6: Embed Role as a Claim in the Application JWT

**User Story:** As a developer, I want the user's role embedded in the existing JWT, so that every request carries the role without an additional Keycloak call.

#### Acceptance Criteria

1. WHEN the JWT_Handler creates an application JWT, THE JWT_Handler SHALL include a Role_Claim containing the user's resolved Role value.
2. THE JWT_Handler SHALL set the Role_Claim to one of `admin`, `viewer_with_query`, or `viewer_without_query`.
3. WHEN the JWT_Handler verifies an application JWT that omits the Role_Claim, THE JWT_Handler SHALL treat the user's Role as the Default_Role.
4. THE JWT_Handler SHALL preserve the existing `sub`, `email`, `exp`, and `iat` claims when adding the Role_Claim.
5. THE JWT_Handler SHALL continue to sign tokens using the configured signing algorithm and secret.

### Requirement 7: Expose the Current User's Role Through the Auth Layer

**User Story:** As a frontend developer, I want the backend to expose the current user's role, so that the interface can adapt to the user's permissions.

#### Acceptance Criteria

1. WHEN Auth_Middleware resolves the current user from a valid JWT, THE Auth_Middleware SHALL make the user's Role available to request handlers.
2. WHEN a client requests `/auth/me` with a valid JWT, THE Backend_API SHALL include the user's Role in the response.
3. IF the JWT is missing or invalid, THEN THE Auth_Middleware SHALL return an HTTP 401 Unauthorized response.
4. THE Backend_API SHALL derive the current user's Role from the Role_Claim in the JWT rather than from the RDS_Users_Table.

### Requirement 8: Server-Side Enforcement of Query Visibility

**User Story:** As a security owner, I want the backend to remove the executed SQL query for users not permitted to see it, so that query visibility cannot be bypassed by the frontend.

#### Acceptance Criteria

1. WHEN the Query_Endpoint produces a response for a user whose Role is `viewer_without_query`, THE Query_Endpoint SHALL omit the Query_Executed_Field from the response.
2. WHEN the Query_Endpoint produces a response for a user whose Role is `viewer_with_query`, THE Query_Endpoint SHALL include the Query_Executed_Field in the response.
3. WHEN the Query_Endpoint produces a response for a user whose Role is `admin`, THE Query_Endpoint SHALL include the Query_Executed_Field in the response.
4. THE Query_Endpoint SHALL determine query visibility from the Role carried in the request's JWT.
5. WHERE a response is retrieved from stored conversation history through a session or turn endpoint, THE Backend_API SHALL apply the same query-visibility rule based on the requesting user's Role.

### Requirement 9: Server-Side Enforcement of Admin Capabilities

**User Story:** As a security owner, I want administrative actions restricted to admins, so that viewer roles cannot perform privileged operations.

#### Acceptance Criteria

1. THE Sentra_System SHALL define the Admin capability set as: viewing the Query_Executed_Field for all responses, listing all Authorized_Users, and triggering a user-to-Keycloak synchronization run.
2. WHEN a user whose Role is `admin` requests an administrative operation, THE Backend_API SHALL perform the requested operation.
3. IF a user whose Role is `viewer_with_query` or `viewer_without_query` requests an administrative operation, THEN THE Backend_API SHALL return an HTTP 403 Forbidden response.
4. WHEN the Backend_API denies an administrative operation, THE Backend_API SHALL return a descriptive authorization error message.
5. THE Backend_API SHALL determine administrative authorization from the Role carried in the request's JWT.

### Requirement 10: Default Role Behavior

**User Story:** As a security owner, I want users without an explicit role to receive the most restrictive role, so that access defaults to least privilege.

#### Acceptance Criteria

1. THE Sentra_System SHALL define the Default_Role as `viewer_without_query`.
2. WHEN a user has no explicit Sentra role assigned in Keycloak, THE Sentra_System SHALL treat that user's Role as the Default_Role.
3. WHEN a user's Role is the Default_Role, THE Query_Endpoint SHALL omit the Query_Executed_Field from responses to that user.
4. WHEN a user's Role is the Default_Role, THE Backend_API SHALL deny administrative operations requested by that user.

### Requirement 11: Frontend Role-Aware Rendering

**User Story:** As a viewer who cannot see SQL queries, I want the interface to hide the query view, so that I am not shown controls for data I cannot access.

#### Acceptance Criteria

1. WHEN the Auth_Context loads the current user, THE Auth_Context SHALL make the user's Role available to frontend components.
2. WHILE the current user's Role is `viewer_without_query`, THE ChatMessage_Component SHALL hide the SQL "Query" tab and the executed-query section.
3. WHILE the current user's Role is `viewer_with_query` or `admin`, THE ChatMessage_Component SHALL display the SQL "Query" tab when the Query_Executed_Field is present in a response.
4. THE Frontend SHALL rely on the backend as the authoritative enforcement point for query visibility rather than on hiding alone.
5. WHEN a response received by the Frontend contains no Query_Executed_Field, THE ChatMessage_Component SHALL render the response without the SQL "Query" tab.

### Requirement 12: Migration and Rollout

**User Story:** As a system administrator, I want a controlled rollout that preserves existing sessions, so that introducing RBAC does not lock out current users.

#### Acceptance Criteria

1. WHEN the feature is first deployed, THE Role_Sync_Service SHALL create a Keycloak record with the Default_Role for every existing Authorized_User who has no Keycloak record.
2. WHILE an existing session presents a JWT that omits the Role_Claim, THE Backend_API SHALL treat that session's Role as the Default_Role until the next sign-in.
3. WHEN an administrator changes a user's role in Keycloak, THE Sentra_System SHALL apply the updated Role at the user's next Google sign-in.
4. WHERE the Keycloak integration is disabled by configuration, THE Backend_API SHALL assign the Default_Role to all users and SHALL continue to serve authenticated requests.
5. THE Sentra_System SHALL document the procedure for assigning the `admin` and `viewer_with_query` roles to users in Keycloak.
