import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import * as adminApi from '../services/adminApi'
import ConfirmModal from './ConfirmModal'
import './AdminConsole.css'

function AdminConsole() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [users, setUsers] = useState([])
  const [roles, setRoles] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(null)
  const [warning, setWarning] = useState(null)

  // Add user form state
  const [newEmail, setNewEmail] = useState('')
  const [newRole, setNewRole] = useState('')
  const [addingUser, setAddingUser] = useState(false)

  // Delete confirmation state
  const [deleteTarget, setDeleteTarget] = useState(null)

  // Role change loading state
  const [changingRole, setChangingRole] = useState(null)

  useEffect(() => {
    fetchData()
  }, [])

  useEffect(() => {
    if (success) {
      const timer = setTimeout(() => setSuccess(null), 4000)
      return () => clearTimeout(timer)
    }
  }, [success])

  useEffect(() => {
    if (error) {
      const timer = setTimeout(() => setError(null), 8000)
      return () => clearTimeout(timer)
    }
  }, [error])

  const fetchData = async () => {
    setLoading(true)
    setError(null)
    try {
      const [usersResponse, rolesResponse] = await Promise.all([
        adminApi.getUsers(),
        adminApi.getRoles()
      ])
      setUsers(usersResponse.users || [])
      setRoles(rolesResponse || [])
      if (usersResponse.warning) {
        setWarning(usersResponse.warning)
      } else {
        setWarning(null)
      }
    } catch (err) {
      setError(err.message || 'Failed to load data')
    } finally {
      setLoading(false)
    }
  }

  const handleAddUser = async (e) => {
    e.preventDefault()
    if (!newEmail.trim() || !newRole) return

    setAddingUser(true)
    setError(null)
    try {
      await adminApi.addUser(newEmail.trim(), newRole)
      setSuccess(`User ${newEmail.trim()} added successfully`)
      setNewEmail('')
      setNewRole('')
      await fetchData()
    } catch (err) {
      setError(err.message || 'Failed to add user')
    } finally {
      setAddingUser(false)
    }
  }

  const handleRoleChange = async (email, newRoleValue) => {
    setChangingRole(email)
    setError(null)
    try {
      await adminApi.changeRole(email, newRoleValue)
      setSuccess(`Role updated for ${email}`)
      await fetchData()
    } catch (err) {
      setError(err.message || 'Failed to change role')
    } finally {
      setChangingRole(null)
    }
  }

  const handleDeleteConfirm = async () => {
    if (!deleteTarget) return
    const email = deleteTarget
    setDeleteTarget(null)
    setError(null)
    try {
      const result = await adminApi.deleteUser(email)
      setSuccess(`User ${email} deleted successfully`)
      if (result.warning) {
        setWarning(result.warning)
      }
      await fetchData()
    } catch (err) {
      setError(err.message || 'Failed to delete user')
    }
  }

  const formatDate = (timestamp) => {
    if (!timestamp) return '—'
    const date = new Date(timestamp)
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    })
  }

  const getRoleDisplayName = (roleValue) => {
    const role = roles.find(r => r.value === roleValue)
    return role ? role.display_name : roleValue || 'unknown'
  }

  const isAdmin = (userRow) => userRow.role === 'admin'

  if (loading) {
    return (
      <div className="admin-console">
        <div className="admin-loading">
          <div className="admin-spinner" />
          <p>Loading admin console...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="admin-console">
      <div className="admin-header">
        <button className="admin-back-btn" onClick={() => navigate('/')}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
            <path d="M19 12H5M12 19L5 12L12 5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
          Back to Dashboard
        </button>
        <h1>Admin Console</h1>
        <p className="admin-subtitle">Manage users and role assignments</p>
      </div>

      {error && (
        <div className="admin-banner admin-banner-error">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
            <path d="M12 9V13M12 17H12.01M21 12C21 16.9706 16.9706 21 12 21C7.02944 21 3 16.9706 3 12C3 7.02944 7.02944 3 12 3C16.9706 3 21 7.02944 21 12Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
          <span>{error}</span>
          <button className="admin-banner-close" onClick={() => setError(null)}>×</button>
        </div>
      )}

      {success && (
        <div className="admin-banner admin-banner-success">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
            <path d="M9 12L11 14L15 10M21 12C21 16.9706 16.9706 21 12 21C7.02944 21 3 16.9706 3 12C3 7.02944 7.02944 3 12 3C16.9706 3 21 7.02944 21 12Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
          <span>{success}</span>
        </div>
      )}

      {warning && (
        <div className="admin-banner admin-banner-warning">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
            <path d="M10.29 3.86L1.82 18A2 2 0 0 0 3.64 21H20.36A2 2 0 0 0 22.18 18L13.71 3.86A2 2 0 0 0 10.29 3.86ZM12 9V13M12 17H12.01" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
          <span>{warning}</span>
          <button className="admin-banner-close" onClick={() => setWarning(null)}>×</button>
        </div>
      )}

      {/* Add User Form */}
      <div className="admin-card">
        <h2 className="admin-card-title">Add New User</h2>
        <form className="admin-add-form" onSubmit={handleAddUser}>
          <input
            type="email"
            className="admin-input"
            placeholder="Email address"
            value={newEmail}
            onChange={(e) => setNewEmail(e.target.value)}
            required
            disabled={addingUser}
          />
          <select
            className="admin-select"
            value={newRole}
            onChange={(e) => setNewRole(e.target.value)}
            required
            disabled={addingUser}
          >
            <option value="">Select role...</option>
            {roles.map(role => (
              <option key={role.value} value={role.value}>
                {role.display_name}
              </option>
            ))}
          </select>
          <button
            type="submit"
            className="admin-btn admin-btn-primary"
            disabled={addingUser || !newEmail.trim() || !newRole}
          >
            {addingUser ? (
              <>
                <span className="admin-btn-spinner" />
                Adding...
              </>
            ) : (
              'Add User'
            )}
          </button>
        </form>
      </div>

      {/* Users Table */}
      <div className="admin-card">
        <div className="admin-card-header">
          <h2 className="admin-card-title">Users ({users.length})</h2>
          <button className="admin-btn admin-btn-ghost" onClick={fetchData}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
              <path d="M1 4V10H7M23 20V14H17M20.49 9A9 9 0 0 0 5.64 5.64L1 10M23 14L18.36 18.36A9 9 0 0 1 3.51 15" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
            Refresh
          </button>
        </div>
        <div className="admin-table-wrapper">
          <table className="admin-table">
            <thead>
              <tr>
                <th>Email</th>
                <th>Created At</th>
                <th>Role</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.length === 0 ? (
                <tr>
                  <td colSpan="4" className="admin-table-empty">
                    No users found
                  </td>
                </tr>
              ) : (
                users.map(u => (
                  <tr key={u.id || u.email}>
                    <td className="admin-cell-email">
                      {u.email}
                      {u.email === user?.email && (
                        <span className="admin-badge-you">you</span>
                      )}
                    </td>
                    <td className="admin-cell-date">{formatDate(u.created_at)}</td>
                    <td className="admin-cell-role">
                      {isAdmin(u) ? (
                        <span className="admin-role-badge admin-role-admin">Admin</span>
                      ) : (
                        <select
                          className="admin-role-select"
                          value={u.role || ''}
                          onChange={(e) => handleRoleChange(u.email, e.target.value)}
                          disabled={changingRole === u.email}
                        >
                          {roles.map(role => (
                            <option key={role.value} value={role.value}>
                              {role.display_name}
                            </option>
                          ))}
                          {u.role === 'unknown' && (
                            <option value="unknown" disabled>Unknown</option>
                          )}
                        </select>
                      )}
                      {changingRole === u.email && (
                        <span className="admin-role-loading" />
                      )}
                    </td>
                    <td className="admin-cell-actions">
                      {isAdmin(u) ? (
                        <span className="admin-protected-text">Protected</span>
                      ) : (
                        <button
                          className="admin-btn admin-btn-danger"
                          onClick={() => setDeleteTarget(u.email)}
                        >
                          Delete
                        </button>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Delete Confirmation Modal */}
      <ConfirmModal
        isOpen={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        onConfirm={handleDeleteConfirm}
        title="Delete User"
        message={`Are you sure you want to delete ${deleteTarget}? This will remove them from both the login allow-list and Keycloak. This action cannot be undone.`}
        confirmText="Delete"
        cancelText="Cancel"
        type="danger"
      />
    </div>
  )
}

export default AdminConsole
