# Implementation Plan: Admin User Management

## Overview

This plan implements the Admin Console for User Management — a full CRUD interface for administrators to manage users and role assignments across RDS and Keycloak. The implementation proceeds bottom-up: schemas → service layer → API endpoints → frontend components → wiring and integration.

## Tasks

- [x] 1. Create Pydantic schemas and extend KeycloakClient
  - [x] 1.1 Create `BackendAPI/admin_schemas.py` with request/response models
    - Define `AddUserRequest` with `EmailStr` and role validation
    - Define `ChangeRoleRequest` with role validation
    - Define `UserWithRole`, `ListUsersResponse`, `RoleInfo`, `DeleteUserResponse`, `ErrorResponse` response models
    - Validate role is one of `viewer_with_query`, `viewer_without_query` (Assignable_Role)
    - _Requirements: 2.5, 2.7, 3.5, 4.4, 8.1, 8.2, 8.3_

  - [x] 1.2 Add `delete_user` and `remove_realm_roles` methods to `BackendAPI/auth/keycloak_client.py`
    - Implement `delete_user(email)` that looks up user by email and deletes from Keycloak
    - Implement `remove_realm_roles(user_id, role_names)` that removes specified realm roles from a user
    - Both methods raise `KeycloakUnavailable` on failure
    - _Requirements: 3.2, 5.2_

- [x] 2. Implement admin service layer
  - [x] 2.1 Create `BackendAPI/admin_service.py` with `AdminService` class
    - Implement `list_users_with_roles(db, keycloak_client)` — query all users from RDS sorted by `created_at` DESC, enrich with Keycloak roles, degrade gracefully if Keycloak unavailable
    - Implement `add_user(db, keycloak_client, email, role)` — check duplicate, insert RDS in transaction, create Keycloak user, assign role, rollback RDS on Keycloak failure
    - Implement `change_user_role(db, keycloak_client, email, new_role)` — verify user exists in RDS, check not admin, remove old roles, assign new role in Keycloak
    - Implement `delete_user(db, keycloak_client, email)` — verify user exists in RDS, check not admin, delete from RDS, attempt Keycloak deletion (warn on failure)
    - Implement `get_assignable_roles()` — return list of `RoleInfo` for `viewer_with_query` and `viewer_without_query`
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.6, 3.1, 3.2, 3.3, 3.6, 4.1, 4.2, 5.1, 5.2, 5.3, 5.4, 5.5, 7.1, 7.2, 7.4, 9.1, 9.2, 9.3, 9.4_

- [x] 3. Add admin API endpoints to FastAPI
  - [x] 3.1 Add admin endpoints to `BackendAPI/Agent_Trigger.py`
    - Replace existing `GET /admin/users` with new implementation that returns `ListUsersResponse` with Keycloak roles
    - Add `POST /admin/users` endpoint that calls `AdminService.add_user`
    - Add `PUT /admin/users/{email}/role` endpoint that calls `AdminService.change_user_role`
    - Add `DELETE /admin/users/{email}` endpoint that calls `AdminService.delete_user`
    - Add `GET /admin/roles` endpoint that calls `AdminService.get_assignable_roles`
    - All endpoints guarded by `require_admin` dependency
    - Import and use `admin_schemas` for request/response validation
    - _Requirements: 2.8, 3.7, 4.3, 5.6, 7.3, 8.4, 8.5_

- [x] 4. Implement frontend admin components
  - [x] 4.1 Create `Frontend/src/services/adminApi.js` admin API client
    - Implement `getUsers()` → GET /admin/users
    - Implement `addUser(email, role)` → POST /admin/users
    - Implement `changeRole(email, role)` → PUT /admin/users/{email}/role
    - Implement `deleteUser(email)` → DELETE /admin/users/{email}
    - Implement `getRoles()` → GET /admin/roles
    - All requests include credentials (HTTP-only cookie)
    - _Requirements: 6.5, 6.6, 6.7, 6.8_

  - [x] 4.2 Create `Frontend/src/components/AdminRoute.jsx` route guard
    - Check user role from AuthContext
    - If role is `admin`, render children
    - If role is not `admin`, redirect to `/`
    - _Requirements: 6.2, 6.3, 6.4_

  - [x] 4.3 Create `Frontend/src/components/AdminConsole.jsx` and `AdminConsole.css`
    - Fetch and display user table (email, created_at, role) on mount
    - Implement add-user form with email input and role selector (populated from GET /admin/roles)
    - Implement inline role change via dropdown selector per user row
    - Implement delete button with confirmation modal before executing
    - Show loading states, error messages, and success feedback
    - Refresh user table after add/edit/delete operations
    - _Requirements: 6.5, 6.6, 6.7, 6.8_

- [x] 5. Wire frontend routes and navigation
  - [x] 5.1 Update `Frontend/src/App.jsx` to add `/admin` route
    - Import `AdminRoute` and `AdminConsole`
    - Add route: `/admin` wrapped in `ProtectedRoute` → `AdminRoute` → `AdminConsole`
    - _Requirements: 6.1_

  - [x] 5.2 Update `Frontend/src/components/UserProfile.jsx` to add admin console button
    - Add "Admin Console" button visible only when user role is `admin`
    - Button navigates to `/admin`
    - _Requirements: 6.2, 6.9_

## Notes

- Each task references specific requirements for traceability
- The existing `POST /admin/keycloak/sync` endpoint is preserved (not replaced)
