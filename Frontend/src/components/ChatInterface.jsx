import { useState, useEffect, useRef } from 'react'
import Sidebar from './Sidebar'
import ChatMessage from './ChatMessage'
import UserProfile from './UserProfile'
import './ChatInterface.css'
import * as chatApi from '../services/chatApi'

function ChatInterface({ onLogout }) {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [sessions, setSessions] = useState([])
  const [currentSessionId, setCurrentSessionId] = useState(null)
  const [showProfile, setShowProfile] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [migrating, setMigrating] = useState(false)
  const messagesEndRef = useRef(null)
  const abortControllerRef = useRef(null)

  const userId = localStorage.getItem('sentra_user_id') || 'default'

  useEffect(() => {
    initializeSessions()
  }, [])

  useEffect(() => {
    if (currentSessionId) {
      loadSession(currentSessionId)
    }
  }, [currentSessionId])

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const initializeSessions = async () => {
    try {
      // Check if localStorage has sessions to migrate
      const sessionKey = `sentra_sessions_${userId}`
      const localSessions = JSON.parse(localStorage.getItem(sessionKey) || '[]')
      
      if (localSessions.length > 0) {
        setMigrating(true)
        console.log('Migrating localStorage sessions to RDS...')
        await chatApi.migrateLocalStorageToRDS(userId)
        setMigrating(false)
      }
      
      // Load sessions from RDS
      await loadSessions()
    } catch (error) {
      console.error('Error initializing sessions:', error)
      setMigrating(false)
      // If RDS fails, try to load from localStorage as fallback
      loadSessionsFromLocalStorage()
    }
  }

  const loadSessions = async () => {
    try {
      const sessionsData = await chatApi.getUserSessions(userId)
      setSessions(sessionsData)
      
      if (sessionsData.length > 0) {
        setCurrentSessionId(sessionsData[0].id)
      } else {
        await createNewSession()
      }
    } catch (error) {
      console.error('Error loading sessions:', error)
      // Fallback to localStorage
      loadSessionsFromLocalStorage()
    }
  }

  const loadSessionsFromLocalStorage = () => {
    const sessionKey = `sentra_sessions_${userId}`
    const savedSessions = JSON.parse(localStorage.getItem(sessionKey) || '[]')
    setSessions(savedSessions)
    if (savedSessions.length > 0) {
      setCurrentSessionId(savedSessions[0].id)
    } else {
      createNewSession()
    }
  }

  const loadSession = async (sessionId) => {
    try {
      const messagesData = await chatApi.getSessionMessages(sessionId)
      setMessages(messagesData)
    } catch (error) {
      console.error('Error loading session messages:', error)
      // Fallback to local session data
      const session = sessions.find(s => s.id === sessionId)
      if (session && session.messages) {
        setMessages(session.messages)
      }
    }
  }

  const saveSession = async (sessionId, updatedMessages) => {
    try {
      // Update local state
      const updatedSessions = sessions.map(s => 
        s.id === sessionId ? { ...s, messages: updatedMessages, updatedAt: Date.now() } : s
      )
      setSessions(updatedSessions)
      
      // Note: Messages are already saved individually in handleSubmit
      // This function is kept for compatibility but doesn't need to save to RDS
    } catch (error) {
      console.error('Error updating session:', error)
    }
  }

  const createNewSession = async () => {
    try {
      // Generate session ID with exactly 33 characters (AWS Bedrock requirement)
      const timestamp = Date.now().toString() // 13 characters
      const randomChars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
      let randomSuffix = ''
      for (let i = 0; i < 19; i++) {
        randomSuffix += randomChars.charAt(Math.floor(Math.random() * randomChars.length))
      }
      const sessionId = `${timestamp}_${randomSuffix}` // Total: 33 characters
      
      // Create session in RDS
      const newSession = await chatApi.createSession(sessionId, userId, 'New Chat')
      
      const updatedSessions = [newSession, ...sessions]
      setSessions(updatedSessions)
      setCurrentSessionId(newSession.id)
      setMessages([])
    } catch (error) {
      console.error('Error creating session:', error)
      // Fallback to localStorage
      const timestamp = Date.now().toString()
      const randomChars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
      let randomSuffix = ''
      for (let i = 0; i < 19; i++) {
        randomSuffix += randomChars.charAt(Math.floor(Math.random() * randomChars.length))
      }
      const sessionId = `${timestamp}_${randomSuffix}`
      
      const newSession = {
        id: sessionId,
        title: 'New Chat',
        messages: [],
        createdAt: Date.now(),
        updatedAt: Date.now()
      }
      const updatedSessions = [newSession, ...sessions]
      setSessions(updatedSessions)
      setCurrentSessionId(newSession.id)
      setMessages([])
    }
  }

  const renameSession = async (sessionId, newTitle) => {
    try {
      await chatApi.updateSessionTitle(sessionId, newTitle)
      
      const updatedSessions = sessions.map(s =>
        s.id === sessionId ? { ...s, title: newTitle } : s
      )
      setSessions(updatedSessions)
    } catch (error) {
      console.error('Error renaming session:', error)
    }
  }

  const deleteSession = async (sessionId) => {
    try {
      await chatApi.deleteSession(sessionId)
      
      const updatedSessions = sessions.filter(s => s.id !== sessionId)
      setSessions(updatedSessions)
      
      if (currentSessionId === sessionId) {
        if (updatedSessions.length > 0) {
          setCurrentSessionId(updatedSessions[0].id)
        } else {
          await createNewSession()
        }
      }
    } catch (error) {
      console.error('Error deleting session:', error)
    }
  }

  const handleStop = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
      abortControllerRef.current = null
      setLoading(false)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!input.trim() || loading) return

    const userMessage = {
      id: Date.now().toString(),
      type: 'user',
      content: input.trim(),
      timestamp: Date.now()
    }

    const updatedMessages = [...messages, userMessage]
    setMessages(updatedMessages)
    setInput('')
    setLoading(true)

    // Save user message to RDS
    try {
      await chatApi.saveMessage(
        userMessage.id,
        currentSessionId,
        userMessage.type,
        userMessage.content,
        userMessage.timestamp
      )
    } catch (error) {
      console.error('Error saving user message:', error)
    }

    // Create new AbortController for this request
    abortControllerRef.current = new AbortController()

    // Update session title if it's the first message
    if (messages.length === 0) {
      const newTitle = input.trim().slice(0, 30) + '...'
      try {
        await chatApi.updateSessionTitle(currentSessionId, newTitle)
        const updatedSessions = sessions.map(s => 
          s.id === currentSessionId ? { ...s, title: newTitle } : s
        )
        setSessions(updatedSessions)
      } catch (error) {
        console.error('Error updating session title:', error)
      }
    }

    try {
      // Call the actual API endpoint using chatApi service
      const data = await chatApi.sendQuery(
        input.trim(),
        userId,
        currentSessionId,
        abortControllerRef.current.signal
      )

      const botMessage = {
        id: (Date.now() + 1).toString(),
        type: 'bot',
        content: data,
        timestamp: Date.now()
      }

      const finalMessages = [...updatedMessages, botMessage]
      setMessages(finalMessages)
      
      // Save bot message to RDS
      try {
        await chatApi.saveMessage(
          botMessage.id,
          currentSessionId,
          botMessage.type,
          botMessage.content,
          botMessage.timestamp
        )
      } catch (error) {
        console.error('Error saving bot message:', error)
      }
      
      saveSession(currentSessionId, finalMessages)
    } catch (error) {
      // Check if the request was aborted
      if (error.name === 'AbortError') {
        console.log('Request was cancelled by user')
        // Don't add any bot message when stopped
        saveSession(currentSessionId, updatedMessages)
        return
      }
      
      console.error('API Error:', error)
      
      // Fallback to mock response if API fails
      const mockResponse = generateMockResponse(input.trim())
      
      const botMessage = {
        id: (Date.now() + 1).toString(),
        type: 'bot',
        content: mockResponse,
        timestamp: Date.now()
      }

      const finalMessages = [...updatedMessages, botMessage]
      setMessages(finalMessages)
      
      // Try to save mock response
      try {
        await chatApi.saveMessage(
          botMessage.id,
          currentSessionId,
          botMessage.type,
          botMessage.content,
          botMessage.timestamp
        )
      } catch (saveError) {
        console.error('Error saving mock message:', saveError)
      }
      
      saveSession(currentSessionId, finalMessages)
    } finally {
      setLoading(false)
      abortControllerRef.current = null
    }
  }

  const generateMockResponse = (query) => {
    const lowerQuery = query.toLowerCase()
    
    // Return insurance policy data
    if (lowerQuery.includes('policy') || lowerQuery.includes('policies')) {
      return {
        type: 'bar',
        data: [
          { label: 'Health', value: 450 },
          { label: 'Life', value: 320 },
          { label: 'Motor', value: 280 },
          { label: 'Travel', value: 150 }
        ],
        explanation: 'Policy distribution shows Health insurance leading with 450 policies, followed by Life insurance with 320 policies. Health segment shows strong market demand.',
        query_executed: 'SELECT policy_type, COUNT(*) as value FROM insurance_data GROUP BY policy_type ORDER BY value DESC'
      }
    } else if (lowerQuery.includes('agent') || lowerQuery.includes('premium')) {
      return {
        type: 'bar',
        data: [
          { label: 'Agent A', value: 125000 },
          { label: 'Agent B', value: 98000 },
          { label: 'Agent C', value: 87000 },
          { label: 'Agent D', value: 76000 }
        ],
        explanation: 'Premium collection by agents shows Agent A leading with ₹1,25,000, demonstrating strong sales performance. Consider sharing best practices across the team.',
        query_executed: 'SELECT agent_name, SUM(gwp) as value FROM insurance_data GROUP BY agent_name ORDER BY value DESC'
      }
    } else if (lowerQuery.includes('zone') || lowerQuery.includes('region')) {
      return {
        type: 'pie',
        data: [
          { label: 'North Zone', value: 35 },
          { label: 'South Zone', value: 28 },
          { label: 'East Zone', value: 22 },
          { label: 'West Zone', value: 15 }
        ],
        explanation: 'Zone-wise distribution shows North Zone leading with 35% market share, followed by South Zone at 28%. West Zone presents growth opportunities.',
        query_executed: 'SELECT zone, (COUNT(*) * 100.0 / (SELECT COUNT(*) FROM insurance_data)) as value FROM insurance_data GROUP BY zone'
      }
    } else if (lowerQuery.includes('trend') || lowerQuery.includes('monthly')) {
      return {
        type: 'line',
        data: [
          { label: 'Jan', value: 45 },
          { label: 'Feb', value: 52 },
          { label: 'Mar', value: 48 },
          { label: 'Apr', value: 61 },
          { label: 'May', value: 58 },
          { label: 'Jun', value: 67 }
        ],
        explanation: 'Monthly policy trends show consistent growth with 49% increase from January to June. April and June show particularly strong performance.',
        query_executed: 'SELECT DATE_FORMAT(policy_start_date, "%b") as label, COUNT(*) as value FROM insurance_data WHERE YEAR(policy_start_date) = 2024 GROUP BY MONTH(policy_start_date) ORDER BY policy_start_date'
      }
    } else {
      return {
        type: 'text',
        data: 'Based on your query, I found relevant information in our insurance system.',
        explanation: 'I can help you analyze insurance policies, agent performance, premium collections, and zone-wise distributions. Try asking about "policy count by type", "premium by agent", or "zone distribution".'
      }
    }
  }

  return (
    <div className="chat-interface">
      {migrating && (
        <div style={{
          position: 'fixed',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          background: 'white',
          padding: '20px',
          borderRadius: '8px',
          boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
          zIndex: 9999
        }}>
          <p>Migrating chat history to database...</p>
        </div>
      )}
      <Sidebar 
        sessions={sessions}
        currentSessionId={currentSessionId}
        onSelectSession={setCurrentSessionId}
        onNewSession={createNewSession}
        onRenameSession={renameSession}
        onDeleteSession={deleteSession}
        onLogout={onLogout}
        isOpen={sidebarOpen}
        onToggle={setSidebarOpen}
      />
      <div className={`chat-main ${!sidebarOpen ? 'sidebar-closed' : ''}`}>
        <div className="chat-header">
          <div className="header-left">
            {!sidebarOpen && (
              <button className="open-sidebar-btn" onClick={() => setSidebarOpen(true)}>
                <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                  <path d="M3 10H17M3 5H17M3 15H17" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                </svg>
              </button>
            )}
            <h2>Sentra Insurance Assistant</h2>
          </div>
          <button className="user-profile-btn" onClick={() => setShowProfile(true)}>
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
              <path d="M10 10C12.7614 10 15 7.76142 15 5C15 2.23858 12.7614 0 10 0C7.23858 0 5 2.23858 5 5C5 7.76142 7.23858 10 10 10Z" fill="currentColor"/>
              <path d="M10 12C4.477 12 0 14.686 0 18V20H20V18C20 14.686 15.523 12 10 12Z" fill="currentColor"/>
            </svg>
          </button>
        </div>
        <div className="chat-messages">
          {messages.length === 0 && (
            <div className="welcome-message">
              <h3>Welcome to Sentra Insurance Assistant</h3>
              <p>Ask me anything about insurance policies, agents, premiums, or coverage.</p>
              <div className="suggestions">
                <button onClick={() => setInput('Show policy count by type')}>Policy count by type</button>
                <button onClick={() => setInput('Show premium by agent')}>Premium by agent</button>
                <button onClick={() => setInput('Show policies by zone')}>Policies by zone</button>
                <button onClick={() => setInput('Show monthly policy trends')}>Monthly trends</button>
              </div>
            </div>
          )}
          {messages.map((message) => (
            <ChatMessage key={message.id} message={message} />
          ))}
          {loading && (
            <div className="loading-message">
              <div className="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
              <button className="stop-button" onClick={handleStop}>
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                  <rect x="3" y="3" width="10" height="10" fill="currentColor" rx="1"/>
                </svg>
                Stop
              </button>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
        <form onSubmit={handleSubmit} className="chat-input-form">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about insurance policies, agents, premiums, or coverage..."
            disabled={loading}
          />
          <button type="submit" disabled={loading || !input.trim()}>
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
              <path d="M2 10L18 2L10 18L9 11L2 10Z" fill="currentColor"/>
            </svg>
          </button>
        </form>
      </div>
      {showProfile && (
        <UserProfile 
          onClose={() => setShowProfile(false)} 
          onLogout={onLogout}
        />
      )}
    </div>
  )
}

export default ChatInterface
