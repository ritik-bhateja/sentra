import { useState } from 'react'
import './UserProfile.css'

function UserProfile({ onClose, onLogout }) {
  const userId = localStorage.getItem('sentra_user_id') || 'user'
  const [user] = useState({
    name: userId,
    email: `${userId}@sentra.com`,
    role: 'Senior Insurance Analyst',
    department: 'Financial Analytics',
    joinDate: 'January 2023'
  })

  return (
    <div className="profile-overlay" onClick={onClose}>
      <div className="profile-modal" onClick={(e) => e.stopPropagation()}>
        <div className="profile-header">
          <div className="profile-avatar">
            <span>{user.name.split(' ').map(n => n[0]).join('')}</span>
          </div>
          <button className="profile-close" onClick={onClose}>
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
              <path d="M15 5L5 15M5 5L15 15" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
            </svg>
          </button>
        </div>
        
        <div className="profile-content">
          <h2>{user.name}</h2>
          <p className="profile-role">{user.role}</p>
          
          <div className="profile-details">
            <div className="profile-detail-item">
              <span className="detail-label">Email</span>
              <span className="detail-value">{user.email}</span>
            </div>
            <div className="profile-detail-item">
              <span className="detail-label">Department</span>
              <span className="detail-value">{user.department}</span>
            </div>
            <div className="profile-detail-item">
              <span className="detail-label">Member Since</span>
              <span className="detail-value">{user.joinDate}</span>
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
