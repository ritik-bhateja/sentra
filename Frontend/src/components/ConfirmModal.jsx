import { useEffect } from 'react'
import './ConfirmModal.css'

/**
 * ConfirmModal Component
 * 
 * A customizable confirmation modal that matches the application theme.
 * 
 * @param {boolean} isOpen - Controls modal visibility
 * @param {function} onClose - Called when modal should close (cancel/escape)
 * @param {function} onConfirm - Called when user confirms the action
 * @param {string} title - Modal title (default: "Confirm Action")
 * @param {string} message - Modal message (default: "Are you sure you want to proceed?")
 * @param {string} confirmText - Confirm button text (default: "Confirm")
 * @param {string} cancelText - Cancel button text (default: "Cancel")
 * @param {string} type - Modal type: "default", "danger", "warning" (default: "default")
 * 
 * Example usage:
 * ```jsx
 * const [showModal, setShowModal] = useState(false)
 * 
 * <ConfirmModal
 *   isOpen={showModal}
 *   onClose={() => setShowModal(false)}
 *   onConfirm={() => handleDelete()}
 *   title="Delete Item"
 *   message="Are you sure you want to delete this item? This action cannot be undone."
 *   confirmText="Delete"
 *   cancelText="Cancel"
 *   type="danger"
 * />
 * ```
 */
function ConfirmModal({ 
  isOpen, 
  onClose, 
  onConfirm, 
  title = "Confirm Action", 
  message = "Are you sure you want to proceed?",
  confirmText = "Confirm",
  cancelText = "Cancel",
  type = "default" // default, danger, warning
}) {
  // Handle escape key press
  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === 'Escape' && isOpen) {
        onClose()
      }
    }

    if (isOpen) {
      document.addEventListener('keydown', handleEscape)
      // Prevent body scroll when modal is open
      document.body.style.overflow = 'hidden'
    }

    return () => {
      document.removeEventListener('keydown', handleEscape)
      document.body.style.overflow = 'unset'
    }
  }, [isOpen, onClose])

  if (!isOpen) return null

  const handleBackdropClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose()
    }
  }

  const handleConfirm = () => {
    onConfirm()
    onClose()
  }

  const getIcon = () => {
    switch (type) {
      case 'danger':
        return (
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" className="modal-icon danger">
            <path d="M12 9V13M12 17H12.01M21 12C21 16.9706 16.9706 21 12 21C7.02944 21 3 16.9706 3 12C3 7.02944 7.02944 3 12 3C16.9706 3 21 7.02944 21 12Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        )
      case 'warning':
        return (
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" className="modal-icon warning">
            <path d="M10.29 3.86L1.82 18A2 2 0 0 0 3.64 21H20.36A2 2 0 0 0 22.18 18L13.71 3.86A2 2 0 0 0 10.29 3.86ZM12 9V13M12 17H12.01" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        )
      default:
        return (
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" className="modal-icon default">
            <path d="M9 12L11 14L15 10M21 12C21 16.9706 16.9706 21 12 21C7.02944 21 3 16.9706 3 12C3 7.02944 7.02944 3 12 3C16.9706 3 21 7.02944 21 12Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        )
    }
  }

  return (
    <div className="modal-overlay" onClick={handleBackdropClick}>
      <div className="modal-container">
        <div className="modal-content">
          <div className="modal-header">
            <div className="modal-icon-container">
              {getIcon()}
            </div>
            <h3 className="modal-title">{title}</h3>
          </div>
          
          <div className="modal-body">
            <p className="modal-message">{message}</p>
          </div>
          
          <div className="modal-footer">
            <button 
              className="modal-btn modal-btn-cancel" 
              onClick={onClose}
              autoFocus
            >
              {cancelText}
            </button>
            <button 
              className={`modal-btn modal-btn-confirm ${type}`} 
              onClick={handleConfirm}
            >
              {confirmText}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ConfirmModal