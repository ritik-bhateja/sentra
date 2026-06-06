/**
 * Admin API Service
 * Handles all API calls for admin user management
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
      credentials: 'include',
      ...options,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error(`Admin API Error [${endpoint}]:`, error);
    throw error;
  }
}

/**
 * Get all users with their Keycloak roles
 */
export async function getUsers() {
  return apiFetch('/admin/users');
}

/**
 * Add a new user with a specific role
 */
export async function addUser(email, role) {
  return apiFetch('/admin/users', {
    method: 'POST',
    body: JSON.stringify({ email, role }),
  });
}

/**
 * Change a user's role
 */
export async function changeRole(email, role) {
  return apiFetch(`/admin/users/${encodeURIComponent(email)}/role`, {
    method: 'PUT',
    body: JSON.stringify({ role }),
  });
}

/**
 * Delete a user
 */
export async function deleteUser(email) {
  return apiFetch(`/admin/users/${encodeURIComponent(email)}`, {
    method: 'DELETE',
  });
}

/**
 * Get list of assignable roles
 */
export async function getRoles() {
  return apiFetch('/admin/roles');
}
