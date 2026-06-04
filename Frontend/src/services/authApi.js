const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

export async function getCurrentUser() {
  const response = await fetch(`${API_BASE_URL}/auth/me`, {
    credentials: 'include',
  });
  if (!response.ok) throw new Error('Not authenticated');
  return await response.json();
}

export async function logout() {
  const response = await fetch(`${API_BASE_URL}/auth/logout`, {
    method: 'POST',
    credentials: 'include',
  });
  if (!response.ok) throw new Error('Logout failed');
  return await response.json();
}

export async function verifyToken() {
  const response = await fetch(`${API_BASE_URL}/auth/verify`, {
    credentials: 'include',
  });
  return response.ok;
}
