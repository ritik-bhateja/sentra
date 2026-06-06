import { useAuth } from '../contexts/AuthContext'
import { useNavigate } from 'react-router-dom'
import './UserProfile.css'

function UserProfile({ onClose, onLogout }) {
  const { user, role } = useAuth()
  const navigate = useNavigate()
  
  // Extract name from email (first part before @)
  const displayName = user?.email?.split('@')[0] || 'User'
  
  // Get first letter for avatar
  const avatarInitial = displayName.charAt(0).toUpperCase()
  
  // Format join date from user creation timestamp
  const joinDate = user?.created_at 
    ? new Date(user.created_at).toLocaleDateString('en-US', { year: 'numeric', month: 'long' })
    : 'Recently'

  const handleAdminConsole = () => {
    onClose()
    navigate('/admin')
  }

  return (
    <div className="profile-overlay" onClick={onClose}>
      <div className="profile-modal" onClick={(e) => e.stopPropagation()}>
        <div className="profile-header">
          <div className="profile-avatar">
            <span>{avatarInitial}</span>
          </div>
          <button className="profile-close" onClick={onClose}>
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
              <path d="M15 5L5 15M5 5L15 15" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
            </svg>
          </button>
        </div>
        
        <div className="profile-content">
          <h2>{displayName}</h2>
          <p className="profile-role">Insurance Assistant User</p>
          
          <div className="profile-details">
            <div className="profile-detail-item">
              <span className="detail-label">EMAIL</span>
              <span className="detail-value">{user?.email}</span>
            </div>
            <div className="profile-detail-item">
              <span className="detail-label">USER ID</span>
              <span className="detail-value">{user?.id}</span>
            </div>
            <div className="profile-detail-item">
              <span className="detail-label">MEMBER SINCE</span>
              <span className="detail-value">{joinDate}</span>
            </div>
          </div>
        </div>

        <div className="profile-footer">
          {role === 'admin' && (
            <button className="profile-admin-btn" onClick={handleAdminConsole}>
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <path d="M10 2C6 2 2 6 2 10C2 14 6 18 10 18C14 18 18 14 18 10C18 6 14 2 10 2ZM10 6C11.1 6 12 6.9 12 8C12 9.1 11.1 10 10 10C8.9 10 8 9.1 8 8C8 6.9 8.9 6 10 6ZM10 16C7.8 16 5.8 14.9 4.6 13.2C4.6 11.6 7.3 10.7 10 10.7C12.7 10.7 15.4 11.6 15.4 13.2C14.2 14.9 12.2 16 10 16Z" fill="currentColor"/>
              </svg>
              Admin Console
            </button>
          )}
          <button className="profile-logout-btn" onClick={onLogout}>
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
              <path d="M7 17H4C3.46957 17 2.96086 16.7893 2.58579 16.4142C2.21071 16.0391 2 15.5304 2 15V5C2 4.46957 2.21071 3.96086 2.58579 3.58579C2.96086 3.21071 3.46957 3 4 3H7M13 13L17 9M17 9L13 5M17 9H7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
            Sign Out
          </button>
        </div>
      </div>
    </div>
  )
}

export default UserProfile
