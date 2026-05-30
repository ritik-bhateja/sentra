/**
 * Simple Markdown Parser for Text Responses
 * 
 * This utility provides basic markdown parsing functionality to convert
 * markdown-style text into formatted HTML elements for better readability.
 */

import React from 'react'

/**
 * Parses markdown text and returns React elements
 * @param {string} text - The markdown text to parse
 * @returns {Array} Array of React elements
 */
export function parseMarkdown(text) {
  if (!text || typeof text !== 'string') return [text]

  const lines = text.split('\n')
  const elements = []
  let currentParagraph = []
  let listItems = []
  let isInList = false

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim()
    
    // Skip empty lines
    if (line === '') {
      if (currentParagraph.length > 0) {
        elements.push(...createParagraphWithLineBreaks(currentParagraph.join(' '), elements.length))
        currentParagraph = []
      }
      if (isInList && listItems.length > 0) {
        elements.push(createList(listItems, elements.length))
        listItems = []
        isInList = false
      }
      continue
    }

    // Parse headers
    if (line.startsWith('#')) {
      // Finish current paragraph or list
      if (currentParagraph.length > 0) {
        elements.push(...createParagraphWithLineBreaks(currentParagraph.join(' '), elements.length))
        currentParagraph = []
      }
      if (isInList && listItems.length > 0) {
        elements.push(createList(listItems, elements.length))
        listItems = []
        isInList = false
      }

      const headerMatch = line.match(/^(#{1,6})\s+(.+)$/)
      if (headerMatch) {
        const level = headerMatch[1].length
        const text = headerMatch[2]
        elements.push(createHeader(text, level, elements.length))
        continue
      }
    }

    // Parse list items
    if (line.startsWith('- ') || line.startsWith('* ') || line.match(/^\d+\.\s/)) {
      // Finish current paragraph
      if (currentParagraph.length > 0) {
        elements.push(...createParagraphWithLineBreaks(currentParagraph.join(' '), elements.length))
        currentParagraph = []
      }

      const listText = line.replace(/^[-*]\s+/, '').replace(/^\d+\.\s+/, '')
      listItems.push(listText)
      isInList = true
      continue
    }

    // Regular text line
    if (isInList && listItems.length > 0) {
      elements.push(createList(listItems, elements.length))
      listItems = []
      isInList = false
    }

    currentParagraph.push(line)
  }

  // Handle remaining content
  if (currentParagraph.length > 0) {
    elements.push(...createParagraphWithLineBreaks(currentParagraph.join(' '), elements.length))
  }
  if (isInList && listItems.length > 0) {
    elements.push(createList(listItems, elements.length))
  }

  return elements.length > 0 ? elements : [text]
}

/**
 * Creates a header element
 * @param {string} text - Header text
 * @param {number} level - Header level (1-6)
 * @param {number} key - React key
 * @returns {React.Element}
 */
function createHeader(text, level, key) {
  const formattedText = parseInlineFormatting(text)
  const className = `markdown-header markdown-h${level}`
  
  switch (level) {
    case 1:
      return <h1 key={key} className={className}>{formattedText}</h1>
    case 2:
      return <h2 key={key} className={className}>{formattedText}</h2>
    case 3:
      return <h3 key={key} className={className}>{formattedText}</h3>
    case 4:
      return <h4 key={key} className={className}>{formattedText}</h4>
    case 5:
      return <h5 key={key} className={className}>{formattedText}</h5>
    case 6:
      return <h6 key={key} className={className}>{formattedText}</h6>
    default:
      return <h2 key={key} className={className}>{formattedText}</h2>
  }
}

/**
 * Creates a paragraph element
 * @param {string} text - Paragraph text
 * @param {number} key - React key
 * @returns {React.Element}
 */
function createParagraph(text, key) {
  const formattedText = parseInlineFormatting(text)
  return <p key={key} className="markdown-paragraph">{formattedText}</p>
}

/**
 * Creates paragraphs with automatic line breaks based on sentence structure
 * @param {string} text - Text to break into lines
 * @param {number} startKey - Starting key for React elements
 * @returns {Array} Array of paragraph elements
 */
function createParagraphWithLineBreaks(text, startKey) {
  if (!text || typeof text !== 'string') return []

  // Split text into sentences based on various patterns
  const sentences = splitIntoSentences(text)
  const elements = []
  
  sentences.forEach((sentence, index) => {
    if (sentence.trim()) {
      const formattedText = parseInlineFormatting(sentence.trim())
      elements.push(
        <p key={startKey + index} className="markdown-paragraph markdown-line">
          {formattedText}
        </p>
      )
    }
  })

  return elements
}

/**
 * Splits text into sentences for better line breaks
 * @param {string} text - Text to split
 * @returns {Array} Array of sentences
 */
function splitIntoSentences(text) {
  if (!text || typeof text !== 'string') return [text]

  // Patterns to split on:
  // 1. Colons followed by bold text (section headers)
  // 2. Periods followed by bold text or capital letters (but NOT decimal numbers)
  // 3. Exclamation marks
  // 4. Question marks
  // 5. Colons at the end of phrases (like "Champion Performance:")
  
  const sentences = []
  let currentSentence = ''
  let i = 0
  
  while (i < text.length) {
    const char = text[i]
    const nextChars = text.slice(i, i + 10)
    
    currentSentence += char
    
    // Check for colon followed by bold text or new section
    if (char === ':' && (
      nextChars.includes('**') || // Colon followed by bold text
      /:\s*[A-Z]/.test(text.slice(i, i + 5)) || // Colon followed by capital letter
      i === text.length - 1 // Colon at end
    )) {
      sentences.push(currentSentence)
      currentSentence = ''
      i++
      continue
    }
    
    // Check for period - but avoid breaking at decimal numbers
    if (char === '.' && i < text.length - 1) {
      const beforePeriod = text.slice(Math.max(0, i - 3), i)
      const afterPeriod = text.slice(i + 1, i + 10)
      
      // Don't break if this is a decimal number (digit before and after period)
      const isDecimal = /\d$/.test(beforePeriod) && /^\d/.test(afterPeriod)
      
      if (!isDecimal && (/^\s+[A-Z]/.test(afterPeriod) || afterPeriod.includes('**'))) {
        sentences.push(currentSentence)
        currentSentence = ''
        i++
        continue
      }
    }
    
    // Check for exclamation or question marks
    if ((char === '!' || char === '?') && i < text.length - 1) {
      const afterMark = text.slice(i + 1, i + 5)
      if (/^\s+[A-Z]/.test(afterMark) || afterMark.includes('**')) {
        sentences.push(currentSentence)
        currentSentence = ''
        i++
        continue
      }
    }
    
    i++
  }
  
  // Add remaining text
  if (currentSentence.trim()) {
    sentences.push(currentSentence)
  }
  
  return sentences.filter(sentence => sentence.trim().length > 0)
}

/**
 * Creates a list element
 * @param {Array} items - List items
 * @param {number} key - React key
 * @returns {React.Element}
 */
function createList(items, key) {
  return (
    <ul key={key} className="markdown-list">
      {items.map((item, index) => (
        <li key={index} className="markdown-list-item">
          {parseInlineFormatting(item)}
        </li>
      ))}
    </ul>
  )
}

/**
 * Parses inline formatting like bold text, numbers, etc.
 * @param {string} text - Text to parse
 * @returns {Array} Array of text and React elements
 */
function parseInlineFormatting(text) {
  if (!text || typeof text !== 'string') return text

  const parts = []
  let lastIndex = 0

  // Combined patterns for inline formatting
  const patterns = [
    // Bold text **text**
    {
      regex: /\*\*([^*]+)\*\*/g,
      formatter: (match, content, index) => (
        <strong key={`bold-${index}`} className="markdown-bold">
          {content}
        </strong>
      )
    },
    // Currency values with Indian Rupee symbol
    {
      regex: /(₹[\d,]+(?:\.\d{2})?)/g,
      formatter: (match, content, index) => (
        <span key={`currency-${index}`} className="markdown-currency">
          {content}
        </span>
      )
    },
    // Numbers with context (e.g., "150 customers", "30.4% premium")
    {
      regex: /(\d+(?:,\d{3})*(?:\.\d+)?%?)\s*(customers?|policies?|accounts?|users?|records?|items?|people|persons?|cases?|claims?|transactions?|premium|lead|gap|performers?)?/gi,
      formatter: (match, number, context, index) => (
        <span key={`metric-${index}`} className="markdown-metric">
          {number}{context ? ` ${context}` : ''}
        </span>
      )
    },
    // Standalone percentages
    {
      regex: /(\d+(?:\.\d+)?%)/g,
      formatter: (match, content, index) => (
        <span key={`percentage-${index}`} className="markdown-percentage">
          {content}
        </span>
      )
    }
  ]

  // Find all matches
  const allMatches = []
  patterns.forEach((pattern, patternIndex) => {
    let match
    while ((match = pattern.regex.exec(text)) !== null) {
      allMatches.push({
        start: match.index,
        end: match.index + match[0].length,
        match: match[0],
        content: match[1],
        context: match[2] || '',
        formatter: pattern.formatter,
        patternIndex
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
  filteredMatches.forEach((matchObj, index) => {
    // Add text before the match
    if (matchObj.start > lastIndex) {
      parts.push(text.slice(lastIndex, matchObj.start))
    }

    // Add the formatted match
    if (matchObj.patternIndex === 0) { // Bold text
      parts.push(matchObj.formatter(matchObj.match, matchObj.content, index))
    } else if (matchObj.patternIndex === 2) { // Numbers with context
      parts.push(matchObj.formatter(matchObj.match, matchObj.content, matchObj.context, index))
    } else { // Other patterns
      parts.push(matchObj.formatter(matchObj.match, matchObj.content, index))
    }

    lastIndex = matchObj.end
  })

  // Add remaining text
  if (lastIndex < text.length) {
    parts.push(text.slice(lastIndex))
  }

  return parts.length > 1 ? parts : text
}

/**
 * Detects if text contains markdown formatting
 * @param {string} text - Text to check
 * @returns {boolean} True if markdown formatting is detected
 */
export function hasMarkdownFormatting(text) {
  if (!text || typeof text !== 'string') return false

  // Check for common markdown patterns
  const markdownPatterns = [
    /^#{1,6}\s+.+$/m,  // Headers
    /\*\*[^*]+\*\*/,   // Bold text
    /^[-*]\s+.+$/m,    // Bullet lists
    /^\d+\.\s+.+$/m    // Numbered lists
  ]

  return markdownPatterns.some(pattern => pattern.test(text))
}

/**
 * Main function to format text with markdown support
 * @param {string} text - Text to format
 * @returns {React.Element|string} Formatted content
 */
export function formatMarkdownText(text) {
  if (!text || typeof text !== 'string') return text

  // Check if text has markdown formatting
  if (hasMarkdownFormatting(text)) {
    const elements = parseMarkdown(text)
    return (
      <div className="markdown-content">
        {elements}
      </div>
    )
  }

  // Fallback to inline formatting only
  return (
    <div className="markdown-content">
      <p className="markdown-paragraph">
        {parseInlineFormatting(text)}
      </p>
    </div>
  )
}