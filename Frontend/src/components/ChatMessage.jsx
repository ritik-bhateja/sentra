import { useState, useRef, useEffect } from 'react'
import ChartView from './ChartView'
import { formatMarkdownText, hasMarkdownFormatting } from '../utils/markdownParser.jsx'
import { useAuth } from '../contexts/AuthContext'
import './ChatMessage.css'

// Import parseInlineFormatting for rendering bold text and formatting
function parseInlineFormatting(text) {
  if (!text || typeof text !== 'string') return text

  const parts = []
  let lastIndex = 0
  let keyCounter = 0

  // Pattern for bold text **text** - matches any content between ** **
  const boldRegex = /\*\*(.+?)\*\*/g
  let match

  while ((match = boldRegex.exec(text)) !== null) {
    // Add text before the match
    if (match.index > lastIndex) {
      const textBefore = text.slice(lastIndex, match.index)
      if (textBefore) {
        parts.push(textBefore)
      }
    }

    // Add the bold text
    parts.push(
      <strong key={`bold-${keyCounter++}`} className="markdown-bold">
        {match[1]}
      </strong>
    )

    lastIndex = match.index + match[0].length
  }

  // Add remaining text
  if (lastIndex < text.length) {
    const remainingText = text.slice(lastIndex)
    if (remainingText) {
      parts.push(remainingText)
    }
  }

  return parts.length > 0 ? parts : text
}

// Parse nudge text with colored sections for "The Issue:" and "Root Cause:"
function parseNudgeWithColors(text) {
  if (!text || typeof text !== 'string') return text

  const parts = []
  let keyCounter = 0

  // Handle both pipe-separated and newline-separated formats
  let lines;
  if (text.includes(' | ')) {
    // Pipe-separated format - split by pipes and treat each as a line
    lines = text.split(' | ').map(line => line.trim());
  } else {
    // Newline-separated format (fallback)
    lines = text.split('\n');
  }
  
  lines.forEach((line, lineIndex) => {
    if (!line.trim()) {
      // Skip empty lines to reduce spacing
      return
    }

    // Check if line contains "The Issue:" or "Root Cause:"
    if (line.includes('**The Issue:**')) {
      const replaced = line.replace('**The Issue:**', '')
      parts.push(
        <div key={`line-${keyCounter++}`} style={{ marginBottom: '6px' }}>
          <strong style={{ color: '#f59e0b', fontWeight: 700 }}>The Issue:</strong>
          {replaced}
        </div>
      )
    } else if (line.includes('**Root Cause:**')) {
      const replaced = line.replace('**Root Cause:**', '')
      parts.push(
        <div key={`line-${keyCounter++}`} style={{ marginBottom: '8px' }}>
          <strong style={{ color: '#3b82f6', fontWeight: 700 }}>Root Cause:</strong>
          {replaced}
        </div>
      )
    } else {
      // Regular line with inline formatting
      parts.push(
        <div key={`line-${keyCounter++}`} style={{ marginBottom: line.startsWith('**') ? '10px' : '4px' }}>
          {parseInlineFormatting(line)}
        </div>
      )
    }
  })

  return parts
}

// Parse CTA content with support for both pipe-separated and newline-separated formats
function parseCTAContent(ctaText) {
  if (!ctaText || typeof ctaText !== 'string') return []

  return ctaText.split(/(?=Action \d+)/g).filter(action => action.trim()).map((action, index) => {
    // Handle both pipe-separated and newline-separated formats
    let actionParts;
    if (action.includes(' | ')) {
      // Pipe-separated format
      actionParts = action.split(' | ').map(part => part.trim());
    } else {
      // Newline-separated format (fallback)
      actionParts = action.trim().split('\n').filter(line => line.trim());
    }
    
    // Parse the action structure (Action with entity name, Priority, Execution, Target)
    let actionTitle = '';
    let priority = '';
    let execution = '';
    let target = '';
    
    actionParts.forEach(part => {
      const trimmedPart = part.trim();
      if (trimmedPart.startsWith('Action')) {
        actionTitle = trimmedPart; // e.g., "Action 1: East Zone — Agent Recruitment"
      } else if (trimmedPart.startsWith('Priority:')) {
        priority = trimmedPart.replace('Priority:', '').trim();
      } else if (trimmedPart.startsWith('Execution:')) {
        execution = trimmedPart.replace('Execution:', '').trim();
      } else if (trimmedPart.startsWith('Target:')) {
        target = trimmedPart.replace('Target:', '').trim();
      }
    });
    
    return {
      index,
      actionTitle,
      priority,
      execution,
      target
    };
  });
}

// SQL Query formatting utility
function formatSQLQuery(query) {
  if (!query || typeof query !== 'string') return query

  // SQL keywords to highlight
  const keywords = [
    'SELECT', 'FROM', 'WHERE', 'JOIN', 'INNER JOIN', 'LEFT JOIN', 'RIGHT JOIN',
    'GROUP BY', 'ORDER BY', 'HAVING', 'LIMIT', 'OFFSET', 'INSERT', 'UPDATE',
    'DELETE', 'CREATE', 'ALTER', 'DROP', 'INDEX', 'TABLE', 'DATABASE',
    'AND', 'OR', 'NOT', 'IN', 'EXISTS', 'BETWEEN', 'LIKE', 'IS', 'NULL',
    'COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'DISTINCT', 'AS', 'ON', 'UNION'
  ]

  let formattedQuery = query
    .replace(/\s+/g, ' ') // Normalize whitespace
    .trim()

  // Add line breaks after major clauses
  const majorClauses = ['SELECT', 'FROM', 'WHERE', 'GROUP BY', 'ORDER BY', 'HAVING', 'LIMIT']
  majorClauses.forEach(clause => {
    const regex = new RegExp(`\\b${clause}\\b`, 'gi')
    formattedQuery = formattedQuery.replace(regex, `\n${clause}`)
  })

  // Add line breaks after JOIN clauses
  const joinClauses = ['JOIN', 'INNER JOIN', 'LEFT JOIN', 'RIGHT JOIN']
  joinClauses.forEach(join => {
    const regex = new RegExp(`\\b${join}\\b`, 'gi')
    formattedQuery = formattedQuery.replace(regex, `\n  ${join}`)
  })

  // Add indentation for AND/OR in WHERE clauses
  formattedQuery = formattedQuery.replace(/\b(AND|OR)\b/gi, '\n  $1')

  // Clean up extra whitespace and normalize
  formattedQuery = formattedQuery
    .split('\n')
    .map(line => line.trim())
    .filter(line => line.length > 0)
    .join('\n')

  return formattedQuery
}

// Copy to clipboard utility
function copyToClipboard(text) {
  if (navigator.clipboard && window.isSecureContext) {
    navigator.clipboard.writeText(text).then(() => {
      // Could add a toast notification here
      console.log('Query copied to clipboard')
    }).catch(err => {
      console.error('Failed to copy query:', err)
    })
  } else {
    // Fallback for older browsers
    const textArea = document.createElement('textarea')
    textArea.value = text
    textArea.style.position = 'fixed'
    textArea.style.left = '-999999px'
    textArea.style.top = '-999999px'
    document.body.appendChild(textArea)
    textArea.focus()
    textArea.select()
    try {
      document.execCommand('copy')
      console.log('Query copied to clipboard')
    } catch (err) {
      console.error('Failed to copy query:', err)
    }
    textArea.remove()
  }
}

// Enhanced content formatting utility with markdown support
function formatTextContent(text) {
  if (!text || typeof text !== 'string') return text

  // Check if text has markdown formatting and use markdown parser
  if (hasMarkdownFormatting(text)) {
    return formatMarkdownText(text)
  }

  // Fallback to original formatting for non-markdown text
  const parts = []
  let lastIndex = 0
  
  // Combined regex for numbers, percentages, currency, and key phrases
  const patterns = [
    // Numbers with context (e.g., "150 policies", "1,250 agents")
    {
      regex: /(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(policies?|agents?|claims?|premiums?|records?|items?|people|persons?|cases?|transactions?)/gi,
      className: 'metric-highlight',
      type: 'metric'
    },
    // Percentages
    {
      regex: /(\d+(?:\.\d+)?%)/g,
      className: 'percentage-highlight',
      type: 'percentage'
    },
    // Currency values
    {
      regex: /(\$\d{1,3}(?:,\d{3})*(?:\.\d{2})?|\d{1,3}(?:,\d{3})*(?:\.\d{2})?\s*(?:dollars?|USD|INR|rupees?))/gi,
      className: 'currency-highlight',
      type: 'currency'
    },
    // Standalone numbers (large numbers)
    {
      regex: /\b(\d{1,3}(?:,\d{3})+(?:\.\d+)?)\b/g,
      className: 'number-highlight',
      type: 'number'
    },
    // Status indicators
    {
      regex: /\b(active|inactive|pending|completed|failed|success|approved|rejected|processing|cancelled|expired)\b/gi,
      className: 'status-highlight',
      type: 'status'
    },
    // Important phrases
    {
      regex: /\b(important|critical|urgent|warning|note|attention|recommended?|suggest(?:ed|ion)?|advice|tip)\b/gi,
      className: 'emphasis-highlight',
      type: 'emphasis'
    }
  ]

  // Find all matches across all patterns
  const allMatches = []
  patterns.forEach(pattern => {
    let match
    while ((match = pattern.regex.exec(text)) !== null) {
      allMatches.push({
        start: match.index,
        end: match.index + match[0].length,
        text: match[0],
        className: pattern.className,
        type: pattern.type
      })
    }
  })

  // Sort matches by position
  allMatches.sort((a, b) => a.start - b.start)

  // Remove overlapping matches (keep the first one)
  const filteredMatches = []
  for (let i = 0; i < allMatches.length; i++) {
    const current = allMatches[i]
    const hasOverlap = filteredMatches.some(existing => 
      (current.start >= existing.start && current.start < existing.end) ||
      (current.end > existing.start && current.end <= existing.end)
    )
    if (!hasOverlap) {
      filteredMatches.push(current)
    }
  }

  // Build the formatted content
  filteredMatches.forEach((match, index) => {
    // Add text before the match
    if (match.start > lastIndex) {
      parts.push(text.slice(lastIndex, match.start))
    }
    
    // Add the highlighted match
    parts.push(
      <span key={`highlight-${index}`} className={match.className} data-type={match.type}>
        {match.text}
      </span>
    )
    
    lastIndex = match.end
  })

  // Add remaining text
  if (lastIndex < text.length) {
    parts.push(text.slice(lastIndex))
  }

  return parts.length > 1 ? parts : text
}

// Expandable Text Component
function ExpandableText({ text, maxLength = 300, className = '' }) {
  const [isExpanded, setIsExpanded] = useState(false)
  const [shouldShowToggle, setShouldShowToggle] = useState(false)
  const contentRef = useRef(null)

  useEffect(() => {
    if (text && text.length > maxLength) {
      setShouldShowToggle(true)
    }
  }, [text, maxLength])

  if (!text) return null

  const needsTruncation = text.length > maxLength
  const displayText = isExpanded ? text : (needsTruncation ? text.slice(0, maxLength) : text)
  
  // Format the display text
  const formattedContent = formatTextContent(displayText)

  return (
    <div className={`expandable-text ${className}`}>
      <div 
        ref={contentRef}
        className={`expandable-content ${isExpanded ? 'expanded' : 'collapsed'}`}
      >
        {formattedContent}
        {needsTruncation && !isExpanded && (
          <span className="truncation-indicator">...</span>
        )}
      </div>
      
      {shouldShowToggle && (
        <button
          className="expand-toggle"
          onClick={() => setIsExpanded(!isExpanded)}
          aria-expanded={isExpanded}
          aria-label={isExpanded ? 'Show less text' : 'Show more text'}
        >
          <span className="toggle-text">
            {isExpanded ? 'Show less' : 'Show more'}
          </span>
          <svg 
            className={`toggle-icon ${isExpanded ? 'rotated' : ''}`}
            width="16" 
            height="16" 
            viewBox="0 0 24 24" 
            fill="none" 
            stroke="currentColor" 
            strokeWidth="2" 
            strokeLinecap="round" 
            strokeLinejoin="round"
          >
            <polyline points="6 9 12 15 18 9"></polyline>
          </svg>
        </button>
      )}
    </div>
  )
}

// Expandable Section Component
function ExpandableSection({ title, children, defaultExpanded = false, icon = '📄' }) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded)
  const contentRef = useRef(null)

  return (
    <div className="expandable-section">
      <button
        className="expandable-trigger"
        onClick={() => setIsExpanded(!isExpanded)}
        aria-expanded={isExpanded}
        aria-label={`${isExpanded ? 'Collapse' : 'Expand'} ${title}`}
      >
        <span className="section-icon">{icon}</span>
        <span className="section-title">{title}</span>
        <svg 
          className={`expand-icon ${isExpanded ? 'rotated' : ''}`}
          width="16" 
          height="16" 
          viewBox="0 0 24 24" 
          fill="none" 
          stroke="currentColor" 
          strokeWidth="2" 
          strokeLinecap="round" 
          strokeLinejoin="round"
        >
          <polyline points="6 9 12 15 18 9"></polyline>
        </svg>
      </button>
      
      <div 
        ref={contentRef}
        className={`expandable-content ${isExpanded ? 'expanded' : 'collapsed'}`}
        style={{
          maxHeight: isExpanded ? `${contentRef.current?.scrollHeight}px` : '0px',
          overflow: 'hidden',
          transition: 'max-height 0.3s ease-in-out, padding 0.3s ease-in-out'
        }}
      >
        <div className="expandable-inner">
          {children}
        </div>
      </div>
    </div>
  )
}

// Trend Summary Component
function TrendSummary({ data }) {
  if (!data || !Array.isArray(data) || data.length === 0) return null

  // Helper function to extract numerical value from currency strings
  const parseNumericValue = (value) => {
    if (typeof value === 'number') return value;
    if (!value) return 0;
    
    // Convert to string and remove currency symbols, commas, and extra spaces
    const cleanValue = String(value)
      .replace(/[₹$£€¥INR USD EUR GBP JPY]/gi, '') // Remove currency symbols
      .replace(/[,\s]/g, '') // Remove commas and spaces
      .replace(/[^\d.-]/g, '') // Keep only digits, dots, and minus signs
      .trim();
    
    // Parse the cleaned value
    const numericValue = parseFloat(cleanValue);
    return isNaN(numericValue) ? 0 : numericValue;
  };

  const values = data.map(item => parseNumericValue(item.value))
  const total = values.reduce((sum, val) => sum + val, 0)
  const average = total / values.length
  const max = Math.max(...values)
  const min = Math.min(...values)
  const maxItem = data[values.indexOf(max)]
  const minItem = data[values.indexOf(min)]

  // Calculate trend (comparing first half vs second half)
  const midPoint = Math.floor(values.length / 2)
  const firstHalfAvg = values.slice(0, midPoint).reduce((sum, val) => sum + val, 0) / midPoint
  const secondHalfAvg = values.slice(midPoint).reduce((sum, val) => sum + val, 0) / (values.length - midPoint)
  const trendPercentage = ((secondHalfAvg - firstHalfAvg) / firstHalfAvg * 100).toFixed(1)
  const isIncreasing = secondHalfAvg > firstHalfAvg

  return (
    <div className="trend-summary">
      <div className="trend-header">
        <div className="explanation-icon">📈</div>
        <span>Trend Analysis</span>
      </div>
      <div className="trend-stats">
        <div className="trend-stat">
          <span className="stat-label">Highest:</span>
          <span className="stat-value">{maxItem.label} ({max.toLocaleString()})</span>
        </div>
        <div className="trend-stat">
          <span className="stat-label">Lowest:</span>
          <span className="stat-value">{minItem.label} ({min.toLocaleString()})</span>
        </div>
        <div className="trend-stat">
          <span className="stat-label">Average:</span>
          <span className="stat-value">{average.toFixed(2).toLocaleString()}</span>
        </div>
        <div className="trend-stat">
          <span className="stat-label">Trend:</span>
          <span className={`stat-value ${isIncreasing ? 'trend-up' : 'trend-down'}`}>
            {isIncreasing ? '↗' : '↘'} {Math.abs(trendPercentage)}%
          </span>
        </div>
      </div>
      <div className="trend-suggestion">
        <strong>Suggestion:</strong> {isIncreasing 
          ? `Positive momentum detected. Consider capitalizing on this upward trend by maintaining current strategies.`
          : `Declining trend observed. Review strategies and consider adjustments to reverse the downward movement.`}
      </div>
    </div>
  )
}

function ChatMessage({ message }) {
  if (message.type === 'user') {
    return (
      <div className="message user-message">
        <div className="message-content">{message.content}</div>
      </div>
    )
  }

  const { content } = message
  
  // Role-based query visibility
  const { role } = useAuth()
  const canViewQuery = role === 'admin' || role === 'viewer_with_query'

  // Determine response type based on the API response structure
  const isChartData = Array.isArray(content.data) && content.type !== 'text'

  // Set default tab based on response type
  // Chart data defaults to 'chart', others default to 'response'
  const defaultTab = isChartData ? 'chart' : 'response'
  const [activeTab, setActiveTab] = useState(defaultTab)

  return (
    <div className="message bot-message">
      <div className="message-content">
        {/* Case 1: Chart data (list of dictionaries) */}
        {isChartData ? (
          <div className="chart-response">
            <div className="tabs-container">
              <button
                className={activeTab === 'chart' ? 'active' : ''}
                onClick={() => setActiveTab('chart')}
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="18" y1="20" x2="18" y2="10"></line>
                  <line x1="12" y1="20" x2="12" y2="4"></line>
                  <line x1="6" y1="20" x2="6" y2="14"></line>
                </svg>
                Chart
              </button>
              <button
                className={activeTab === 'table' ? 'active' : ''}
                onClick={() => setActiveTab('table')}
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                  <line x1="3" y1="9" x2="21" y2="9"></line>
                  <line x1="3" y1="15" x2="21" y2="15"></line>
                  <line x1="9" y1="3" x2="9" y2="21"></line>
                  <line x1="15" y1="3" x2="15" y2="21"></line>
                </svg>
                Table
              </button>
              {canViewQuery && content.query_executed && (
                <button
                  className={activeTab === 'query' ? 'active' : ''}
                  onClick={() => setActiveTab('query')}
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <polyline points="16 18 22 12 16 6"></polyline>
                    <polyline points="8 6 2 12 8 18"></polyline>
                  </svg>
                  Query
                </button>
              )}
              {content.cta && content.cta.trim() !== '' && (
                <button
                  className={activeTab === 'cta' ? 'active' : ''}
                  onClick={() => setActiveTab('cta')}
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
                    <polyline points="22 4 12 14.01 9 11.01"></polyline>
                  </svg>
                  CTA
                </button>
              )}
            </div>
            
            {activeTab === 'chart' && (
              <div className="chart-and-explanation">
                <div className="chart-section">
                  <ChartView type={content.type} data={content.data} />
                  
                  {/* Performance Insight Section - Plain text display below chart */}
                  {content.nudge && content.nudge.trim() !== '' && (
                    <div className="insight-section">
                      <div className="insight-header">
                        <div className="insight-icon">💡</div>
                        <div className="insight-header-text">
                          <h3 className="insight-title">Performance Insight</h3>
                          <p className="insight-subtitle">Data-driven analysis of underperforming entities</p>
                        </div>
                      </div>
                      <div className="insight-content">
                        <div className="insight-text-content">
                          {parseNudgeWithColors(content.nudge)}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
                <div className="explanation-section">
                  <div className="explanation">
                    <div className="explanation-header">
                      <div className="explanation-icon">💡</div>
                      <span>Summary</span>
                    </div>
                    <div className="explanation-text">{content.explanation}</div>
                  </div>
                  <TrendSummary data={content.data} />
                </div>
              </div>
            )}

            {activeTab === 'table' && (
              <div className="table-view">
                <table>
                  <thead>
                    <tr>
                      <th>Label</th>
                      <th>Value</th>
                    </tr>
                  </thead>
                  <tbody>
                    {content.data.map((item, index) => (
                      <tr key={index}>
                        <td>{item.label}</td>
                        <td>{item.value.toLocaleString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {activeTab === 'query' && canViewQuery && content.query_executed && (
              <ExpandableSection 
                title="SQL Query Details" 
                icon="🔍" 
                defaultExpanded={true}
              >
                <div className="enhanced-query-display">
                  <div className="query-header">
                    <div className="query-meta">
                      <span className="query-label">Executed Query:</span>
                      <span className="query-type">SQL</span>
                    </div>
                  </div>
                  <div className="query-code-container">
                    <pre className="query-code">
                      <code>{formatSQLQuery(content.query_executed)}</code>
                    </pre>
                    <button 
                      className="copy-query-btn"
                      onClick={() => copyToClipboard(content.query_executed)}
                      title="Copy query to clipboard"
                    >
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                      </svg>
                    </button>
                  </div>
                </div>
              </ExpandableSection>
            )}

            {activeTab === 'cta' && content.cta && content.cta.trim() !== '' && (
              <div className="cta-tab-content">
                <div className="cta-header">
                  <div className="cta-icon">🎯</div>
                  <h3 className="cta-title">Recommended Actions</h3>
                  <p className="cta-subtitle">Data-driven steps to address underperformance</p>
                </div>
                <div className="cta-content">
                  {parseCTAContent(content.cta).map((actionData) => (
                    <div key={actionData.index} className="cta-action-card-simple">
                      <div className="cta-simple-header">
                        <span className="cta-action-title-crisp">{actionData.actionTitle}</span>
                        <span className={`cta-priority cta-priority-${actionData.priority.toLowerCase()}`}>
                          {actionData.priority}
                        </span>
                      </div>
                      {actionData.execution && (
                        <div className="cta-execution-simple">
                          <span className="cta-label">Execution:</span> {actionData.execution}
                        </div>
                      )}
                      {actionData.target && (
                        <div className="cta-target-simple">
                          <span className="cta-label">Target:</span> {actionData.target}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : /* Case 2: Simple text response */ (
          <div className="text-response">
            {/* Tabs for text response */}
            <div className="tabs-container">
              <button
                className={activeTab === 'response' ? 'active' : ''}
                onClick={() => setActiveTab('response')}
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                </svg>
                Response
              </button>
              {canViewQuery && content.query_executed && (
                <button
                  className={activeTab === 'query' ? 'active' : ''}
                  onClick={() => setActiveTab('query')}
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <polyline points="16 18 22 12 16 6"></polyline>
                    <polyline points="8 6 2 12 8 18"></polyline>
                  </svg>
                  Query
                </button>
              )}
              {content.cta && content.cta.trim() !== '' && (
                <button
                  className={activeTab === 'cta' ? 'active' : ''}
                  onClick={() => setActiveTab('cta')}
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
                    <polyline points="22 4 12 14.01 9 11.01"></polyline>
                  </svg>
                  CTA
                </button>
              )}
            </div>

            {activeTab === 'response' && (
              <div className="enhanced-text-response">
                <div className="response-header">
                  <div className="response-icon">💡</div>
                  <h3 className="response-title">Analysis Result</h3>
                </div>
                
                <div className="response-content">
                  {/* Main content with enhanced formatting */}
                  <div className="main-content">
                    <div className="content-text">
                      <ExpandableText 
                        text={content.explanation || content.data || 'No response available'}
                        maxLength={400}
                        className="formatted-content"
                      />
                    </div>
                  </div>
                  
                  {/* Performance Insight Section - Show directly below response */}
                  {content.nudge && content.nudge.trim() !== '' && (
                    <div className="insight-section">
                      <div className="insight-header">
                        <div className="insight-icon">💡</div>
                        <div className="insight-header-text">
                          <h3 className="insight-title">Performance Insight</h3>
                          <p className="insight-subtitle">Data-driven analysis of underperforming entities</p>
                        </div>
                      </div>
                      <div className="insight-content">
                        <div className="insight-text-content">
                          {parseNudgeWithColors(content.nudge)}
                        </div>
                      </div>
                    </div>
                  )}
                  
                  {/* Metadata section */}
                  <div className="metadata-section">
                    <div className="metadata-item">
                      <span className="metadata-label">Response Type:</span>
                      <span className="metadata-value">Text Analysis</span>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'query' && canViewQuery && content.query_executed && (
              <div className="query-and-nudge-section">
                <ExpandableSection 
                  title="SQL Query Details" 
                  icon="🔍" 
                  defaultExpanded={true}
                >
                  <div className="enhanced-query-display">
                    <div className="query-header">
                      <div className="query-meta">
                        <span className="query-label">Executed Query:</span>
                        <span className="query-type">SQL</span>
                      </div>
                    </div>
                    <div className="query-code-container">
                      <pre className="query-code">
                        <code>{formatSQLQuery(content.query_executed)}</code>
                      </pre>
                      <button 
                        className="copy-query-btn"
                        onClick={() => copyToClipboard(content.query_executed)}
                        title="Copy query to clipboard"
                      >
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                          <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                        </svg>
                      </button>
                    </div>
                  </div>
                </ExpandableSection>
              </div>
            )}

            {activeTab === 'cta' && content.cta && content.cta.trim() !== '' && (
              <div className="cta-tab-content">
                <div className="cta-header">
                  <div className="cta-icon">🎯</div>
                  <h3 className="cta-title">Recommended Actions</h3>
                  <p className="cta-subtitle">Data-driven steps to address underperformance</p>
                </div>
                <div className="cta-content">
                  {parseCTAContent(content.cta).map((actionData) => (
                    <div key={actionData.index} className="cta-action-card-simple">
                      <div className="cta-simple-header">
                        <span className="cta-action-title-crisp">{actionData.actionTitle}</span>
                        <span className={`cta-priority cta-priority-${actionData.priority.toLowerCase()}`}>
                          {actionData.priority}
                        </span>
                      </div>
                      {actionData.execution && (
                        <div className="cta-execution-simple">
                          <span className="cta-label">Execution:</span> {actionData.execution}
                        </div>
                      )}
                      {actionData.target && (
                        <div className="cta-target-simple">
                          <span className="cta-label">Target:</span> {actionData.target}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export default ChatMessage
