# Sentra - Banking & Insurance AI Chatbot UI

A modern, dark-mode AI chatbot interface for banking and insurance data queries, built with React and Vite.

## Features

- 🔐 Simple login page (any credentials work)
- 💬 Natural language query interface
- 📊 Dynamic chart rendering (Bar, Line, Pie, Scatter)
- 📋 Chart/Table toggle view
- 💾 Session persistence with localStorage
- 🎨 Clean, professional dark mode design
- 📱 Responsive layout for desktop and mobile
- ⚡ Typing animation and loading indicators
- 📂 Sidebar with session history
- ✏️ Rename and delete chat sessions
- 🔎 SQL query viewer
- 💡 Performance insights and recommendations
- 🎯 Call-to-action suggestions

## Installation

```bash
npm install
```

## Development

```bash
npm run dev
```

## Build

```bash
npm run build
```

## API Integration

### Setup

1. Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

2. Update the API endpoint in `.env`:
```env
VITE_API_ENDPOINT=https://your-api-id.execute-api.ap-south-1.amazonaws.com/invoke
```

3. For production, update to your deployed backend URL

The application will automatically use this endpoint for all queries.

### Request Format

The application sends POST requests to `/query` endpoint with the following body:
```json
{
  "user_query": "Show sales by quarter",
  "customer_specific": false
}
```

- `user_query`: The user's natural language query
- `customer_specific`: Boolean indicating if customer mode is active

## API Response Formats

### 1. Chart Data Response
```json
{
  "type": "bar|line|pie|scatter",
  "data": [
    {"label": "Label1", "value": 123},
    {"label": "Label2", "value": 456}
  ],
  "explanation": "Explanation text here",
  "query_executed": "SELECT * FROM table",
  "nudge": "Performance insights here",
  "cta": "Action 1: Recommendation | Priority: HIGH | Execution: Steps | Target: Goals"
}
```

### 2. Text Response
```json
{
  "type": "text",
  "data": "Simple text response or aggregate value",
  "explanation": "Explanation text here",
  "query_executed": "SELECT COUNT(*) FROM table"
}
```

**Note:** Customer-specific responses are only for banking data queries. Insurance data has no access restrictions.

## Response Field Details

### Chart Types
- **bar**: Categorical comparisons (policy types, agents, zones)
- **pie**: Percentage distributions (market share, breakdown)
- **line**: Time-series trends (monthly, yearly patterns)
- **scatter**: Correlations (premium vs coverage)

### Additional Fields
- **query_executed**: SQL query used to generate the data (optional)
- **nudge**: Performance insights with "The Issue" and "Root Cause" analysis (optional)
- **cta**: Call-to-action recommendations with Priority, Execution, and Target (optional)

### Nudge Format
Supports both pipe-separated and newline-separated formats:
```
1. Critical Issue | **The Issue:** Description | **Root Cause:** Analysis
```

### CTA Format
Supports both pipe-separated and newline-separated formats:
```
Action 1: Title | Priority: HIGH | Execution: Steps | Target: Goals
```

## Tech Stack

- React 18
- Vite
- Recharts (for data visualization)
- CSS3 (custom styling with glassmorphism)
- LocalStorage (for session persistence)

## Project Structure

```
src/
├── components/
│   ├── Login.jsx/css          # Login page with user selection
│   ├── ChatInterface.jsx/css  # Main chat interface
│   ├── ChatMessage.jsx/css    # Message display with charts
│   ├── ChartView.jsx/css      # Chart rendering (bar, line, pie, scatter)
│   ├── Sidebar.jsx/css        # Chat history sidebar
│   ├── UserProfile.jsx/css    # User profile modal
│   └── ConfirmModal.jsx/css   # Confirmation modal for actions
├── utils/
│   └── markdownParser.jsx     # Markdown text formatting
├── App.jsx
├── main.jsx
└── index.css
```

## Features in Detail

### Chart Visualizations
- Bar charts for comparisons
- Line charts for trends
- Pie charts for distributions
- Scatter plots for correlations
- Toggle between chart and table view
- View SQL queries used to generate data
- Trend analysis with insights

### Performance Insights
- Automatic detection of underperforming entities
- Color-coded issue and root cause analysis
- Data-driven recommendations
- Priority-based action items

### Session Management
- Auto-save conversations to localStorage
- Rename chat sessions
- Delete unwanted chats with confirmation modal
- Session history in sidebar
- Persistent across page reloads
- Search functionality for chat history

### User Interface
- Dark mode with glassmorphism effects
- Smooth animations and transitions
- Responsive design for all screen sizes
- Keyboard shortcuts (Escape to close modals/menus)
- Click-outside-to-close for dropdowns
- Loading states and typing indicators

## Mobile Responsive

Fully optimized for mobile devices with:
- Collapsible sidebar with overlay
- Touch-friendly controls
- Responsive charts
- Optimized spacing and typography
- Hamburger menu navigation
- Swipe gestures support


## Browser Support

- Chrome (recommended)
- Firefox
- Safari
- Edge
- Mobile browsers (iOS Safari, Chrome Mobile)

## Environment Variables

Create a `.env` file in the Frontend directory:

```env
VITE_API_URL=http://localhost:5000
```

For production, update to your deployed backend URL.

## Development Tips

1. **Hot Module Replacement**: Vite provides instant HMR for fast development
2. **Mock Data**: Backend failures gracefully handled with informative error messages
3. **Session Storage**: All chat sessions stored in localStorage for persistence
4. **Debugging**: Open browser DevTools to see API requests and responses

## License

This project is part of the Sentra Banking & Insurance AI Chatbot system.
