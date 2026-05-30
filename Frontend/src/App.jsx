import { useState, useEffect } from 'react'
import Login from './components/Login'
import ChatInterface from './components/ChatInterface'
import './App.css'

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false)

  useEffect(() => {
    const loggedIn = localStorage.getItem('sentra_logged_in')
    if (loggedIn === 'true') {
      setIsLoggedIn(true)
    }
  }, [])

  const handleLogin = (username) => {
    localStorage.setItem('sentra_logged_in', 'true')
    localStorage.setItem('sentra_user_id', username)
    setIsLoggedIn(true)
  }

  const handleLogout = () => {
    localStorage.removeItem('sentra_logged_in')
    localStorage.removeItem('sentra_user_id')
    setIsLoggedIn(false)
  }

  return (
    <div className="app">
      {!isLoggedIn ? (
        <Login onLogin={handleLogin} />
      ) : (
        <ChatInterface onLogout={handleLogout} />
      )}
    </div>
  )
}

export default App
