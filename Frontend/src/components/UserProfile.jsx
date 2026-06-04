import { useAuth } from '../contexts/AuthContext'
import './UserProfile.css'

function UserProfile({ onClose, onLogout }) {
  const { user } = useAuth()
  
  // Extract name from email (first part before @)
  const displayName = user?.email?.split('@')[0] || 'User'
  
  // Get first letter for avatar
  const avatarInitial = displayName.charAt(0).toUpperCase()
  
  // Format join date from user creation timestamp
  const joinDate = user?.created_at 
    ? new Date(user.created_at).toLocaleDateString('en-US', { year: 'numeric', month: 'long' })
    : 'Recently'

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
