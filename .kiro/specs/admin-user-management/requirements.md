# Requirements Document

## Introduction

This feature introduces a **full Admin Console for User Management** in the Sentra Banking & Insurance AI Chatbot. The Admin Console allows administrators to perform CRUD operations on users and their role assignments, with changes synchronized across both RDS (the login allow-list) and Keycloak (the role authority).

Currently, administrators can only list authorized users (`GET /admin/users`) and trigger a user-to-Keycloak sync (`POST /admin/keycloak/sync`). This feature expands admin capabilities to include adding users with a specific role, changing user roles, viewing available roles, and deleting users — all through both backend API endpoints and a dedicated frontend admin UI.

Key design constraints:
- **RDS remains the login allow-list** (role-free). Adding/removing a user means adding/removing their email from the `users` table.
- **Keycloak remains the sole role authority.** Role assignment and changes happen exclusively through Keycloak.
- **Google OAuth2 remains the sole authentication mechanism.** No changes to login flow.
- **The `admin` role is never exposed as an assignable role** in the admin console. Admins can only assign `viewer_with_query` or `viewer_without_query`.
- **Dual deletion** is required: removing a user means removing them from both RDS and Keycloak.
- **Admin capabilities are guarded** by the existing `require_admin` middleware (HTTP 403 for non-admins).

## Glossary

- **Admin_Console**: The frontend page and associated backend endpoints that allow administrators to manage users and their roles.
- **Admin_User**: A user whose Role in Keycloak is `admin`, granting access to administrative operations.
- **Backend_API**: The FastAPI service defined in `BackendAPI/Agent_Trigger.py`.
- **Keycloak_Client**: The backend module (`BackendAPI/auth/keycloak_client.py`) that communicates with the Keycloak Admin REST API.
- **RDS_Users_Table**: The PostgreSQL `users` table that serves as the login allow-list (role-free).
- **Sentra_Realm**: The Keycloak realm dedicated to Sentra that contains user records and role assignments.
- **Role**: A named authorization level. Permitted values: `admin`, `viewer_with_query`, `viewer_without_query`.
- **Assignable_Role**: A role that an administrator can assign or change a user to via the Admin_Console. Permitted values: `viewer_with_query`, `viewer_without_query` (excludes `admin`).
- **Admin_Route**: The dedicated frontend route (`/admin`) that provides access to the Admin_Console UI.
- **Admin_Properties_Page**: The existing user properties page enhanced with a button that redirects administrators to the Admin_Console.
- **Target_User**: The user being created, modified, or deleted by an administrator through the Admin_Console.
- **Query_Executed_Field**: The `query_executed` field in query responses containing the executed SQL statement.
- **Require_Admin_Middleware**: The `require_admin` dependency in `BackendAPI/auth/middleware.py` that enforces admin-only access (returns HTTP 403 for non-admins).

## Requirements

### Requirement 1: Admin Can View Executed Queries

**User Story:** As an admin, I want to see the `query_executed` field in query responses, so that I have full visibility into what SQL is being executed.

#### Acceptance Criteria

1. WHEN the Query Endpoint produces a response for a user whose Role is `admin`, THE Backend_API SHALL include the Query_Executed_Field in the response.
2. THE Admin_Console SHALL not alter the existing query-visibility behavior for the `admin` role.

### Requirement 2: Add User with Specific Role

**User Story:** As an admin, I want to add a new user and assign them a role, so that I can onboard authorized users with the correct permissions in a single operation.

#### Acceptance Criteria

1. WHEN an Admin_User submits a request to add a user with a valid email and an Assignable_Role, THE Backend_API SHALL create a record in the RDS_Users_Table with that email.
2. WHEN an Admin_User submits a request to add a user with a valid email and an Assignable_Role, THE Backend_API SHALL create a corresponding user in the Sentra_Realm in Keycloak.
3. WHEN the Backend_API creates a new Keycloak user, THE Backend_API SHALL assign the specified Assignable_Role to that user in Keycloak.
4. IF the email already exists in the RDS_Users_Table, THEN THE Backend_API SHALL return an HTTP 409 Conflict response with a descriptive error message.
5. IF the specified role is not an Assignable_Role, THEN THE Backend_API SHALL return an HTTP 400 Bad Request response with a descriptive error message.
6. IF the Backend_API cannot reach Keycloak during user creation, THEN THE Backend_API SHALL roll back the RDS insert and return an HTTP 503 Service Unavailable response with a descriptive error message.
7. THE Backend_API SHALL validate that the email follows a valid email format before creating the user.
8. THE Backend_API SHALL guard the add-user endpoint with the Require_Admin_Middleware.

### Requirement 3: Change User Role

**User Story:** As an admin, I want to change an existing user's role, so that I can adjust permissions as business needs change without deleting and re-creating the user.

#### Acceptance Criteria

1. WHEN an Admin_User submits a request to change a Target_User's role to an Assignable_Role, THE Backend_API SHALL update the Target_User's role assignment in Keycloak to the specified role.
2. WHEN the Backend_API changes a role, THE Backend_API SHALL remove the Target_User's previous Sentra realm roles before assigning the new role.
3. IF the Target_User does not exist in the RDS_Users_Table, THEN THE Backend_API SHALL return an HTTP 404 Not Found response with a descriptive error message.
4. IF the Target_User does not exist in Keycloak, THEN THE Backend_API SHALL create the user in Keycloak and assign the specified Assignable_Role.
5. IF the specified role is not an Assignable_Role, THEN THE Backend_API SHALL return an HTTP 400 Bad Request response with a descriptive error message.
6. IF the Target_User's current role is `admin`, THEN THE Backend_API SHALL return an HTTP 403 Forbidden response indicating that admin roles cannot be changed through this endpoint.
7. THE Backend_API SHALL guard the change-role endpoint with the Require_Admin_Middleware.
8. WHEN a role change succeeds, THE Sentra_System SHALL apply the updated role at the Target_User's next Google sign-in.

### Requirement 4: View Available Roles

**User Story:** As an admin, I want to see the available assignable roles for my realm, so that I know which roles I can assign when adding or modifying users.

#### Acceptance Criteria

1. WHEN an Admin_User requests the list of available roles, THE Backend_API SHALL return a list containing only the Assignable_Roles (`viewer_with_query` and `viewer_without_query`).
2. THE Backend_API SHALL exclude the `admin` role from the list of available roles returned to the Admin_Console.
3. THE Backend_API SHALL guard the list-roles endpoint with the Require_Admin_Middleware.
4. THE Backend_API SHALL return each role with a human-readable display name and the role value.

### Requirement 5: Delete User

**User Story:** As an admin, I want to delete a user, so that revoked users lose both login access and their Keycloak identity in a single operation.

#### Acceptance Criteria

1. WHEN an Admin_User submits a request to delete a Target_User, THE Backend_API SHALL remove the Target_User's record from the RDS_Users_Table.
2. WHEN an Admin_User submits a request to delete a Target_User, THE Backend_API SHALL remove the Target_User's record from the Sentra_Realm in Keycloak.
3. IF the Target_User does not exist in the RDS_Users_Table, THEN THE Backend_API SHALL return an HTTP 404 Not Found response with a descriptive error message.
4. IF the Backend_API cannot reach Keycloak during user deletion, THEN THE Backend_API SHALL still remove the user from the RDS_Users_Table and return a warning indicating Keycloak deletion was unsuccessful.
5. IF the Target_User's current role is `admin`, THEN THE Backend_API SHALL return an HTTP 403 Forbidden response indicating that admin users cannot be deleted through this endpoint.
6. THE Backend_API SHALL guard the delete-user endpoint with the Require_Admin_Middleware.
7. WHEN a user is deleted from the RDS_Users_Table, THE Sentra_System SHALL deny login for that email on subsequent Google OAuth attempts.

### Requirement 6: Admin Route in Frontend

**User Story:** As an admin, I want a dedicated admin page accessible from my user interface, so that I can manage users without leaving the application.

#### Acceptance Criteria

1. THE Frontend SHALL provide a dedicated route at `/admin` that renders the Admin_Console UI.
2. WHILE the current user's Role is `admin`, THE Frontend SHALL display a navigation element that links to the Admin_Route.
3. WHILE the current user's Role is not `admin`, THE Frontend SHALL hide the navigation element that links to the Admin_Route.
4. IF a non-admin user navigates directly to `/admin`, THEN THE Frontend SHALL redirect the user to the main application page.
5. THE Admin_Console UI SHALL display a table of all authorized users with their email, creation date, and current role from Keycloak.
6. THE Admin_Console UI SHALL provide a form to add a new user with an email field and a role selector populated with Assignable_Roles.
7. THE Admin_Console UI SHALL provide a control to change the role of an existing user using a selector populated with Assignable_Roles.
8. THE Admin_Console UI SHALL provide a control to delete a user, with a confirmation prompt before executing deletion.
9. THE Admin_Properties_Page SHALL display a button that redirects the Admin_User to the Admin_Route.

### Requirement 7: Admin Users Listing with Roles

**User Story:** As an admin, I want to see a combined view of users with their Keycloak roles, so that I have full context when managing user permissions.

#### Acceptance Criteria

1. WHEN an Admin_User requests the user list, THE Backend_API SHALL return each user's email, RDS record metadata (id, created_at, last_login), and their current role from Keycloak.
2. IF Keycloak is unreachable during user listing, THEN THE Backend_API SHALL return users from the RDS_Users_Table with the role field set to "unknown" and include a warning in the response.
3. THE Backend_API SHALL guard the user-listing endpoint with the Require_Admin_Middleware.
4. THE Backend_API SHALL return users sorted by creation date in descending order.

### Requirement 8: Input Validation and Error Handling

**User Story:** As an admin, I want clear error messages when operations fail, so that I can understand what went wrong and take corrective action.

#### Acceptance Criteria

1. IF an admin operation receives an invalid email format, THEN THE Backend_API SHALL return an HTTP 400 Bad Request response specifying that the email format is invalid.
2. IF an admin operation receives an empty or missing email, THEN THE Backend_API SHALL return an HTTP 400 Bad Request response specifying that email is required.
3. IF an admin operation receives an empty or missing role, THEN THE Backend_API SHALL return an HTTP 400 Bad Request response specifying that role is required.
4. IF a non-admin user requests any admin endpoint, THEN THE Backend_API SHALL return an HTTP 403 Forbidden response with the message "Admin privileges required for this operation".
5. WHEN any admin operation encounters an unexpected server error, THE Backend_API SHALL return an HTTP 500 Internal Server Error response with a descriptive error message and SHALL log the full error details.

### Requirement 9: Atomicity and Consistency

**User Story:** As an admin, I want user operations to be consistent across RDS and Keycloak, so that the system does not end up in a partial state.

#### Acceptance Criteria

1. WHEN the add-user operation succeeds in RDS but fails in Keycloak, THE Backend_API SHALL roll back the RDS insert so that no orphan record exists.
2. WHEN the delete-user operation succeeds in RDS but fails in Keycloak, THE Backend_API SHALL complete the RDS deletion and return a warning that the Keycloak record may still exist.
3. THE Backend_API SHALL use database transactions for all RDS write operations to ensure atomicity.
4. WHEN a role-change operation fails in Keycloak, THE Backend_API SHALL return an error without modifying any data, leaving the user's role unchanged.
