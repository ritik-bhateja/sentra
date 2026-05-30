import { useState, useEffect, useRef } from 'react'
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, ScatterChart, Scatter,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell
} from 'recharts'
import './ChartView.css'

const COLORS = ['#10b981', '#3b82f6', '#8b5cf6', '#f59e0b', '#ef4444', '#06b6d4']

function ChartView({ type, data }) {
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 })
  const containerRef = useRef(null)

  useEffect(() => {
    const updateDimensions = () => {
      if (containerRef.current) {
        const width = containerRef.current.offsetWidth
        const isMobile = window.innerWidth <= 768
        setDimensions({
          width: width - 32, // subtract padding
          height: isMobile ? 300 : 320
        })
      }
    }
    
    // Initial update
    setTimeout(updateDimensions, 100)
    
    window.addEventListener('resize', updateDimensions)
    return () => window.removeEventListener('resize', updateDimensions)
  }, [])

  // Ensure data is valid
  if (!data || !Array.isArray(data) || data.length === 0) {
    return (
      <div className="chart-container" ref={containerRef}>
        <div className="chart-error">No data available</div>
      </div>
    )
  }

  if (dimensions.width === 0) {
    return (
      <div className="chart-container" ref={containerRef}>
        <div className="chart-error">Loading chart...</div>
      </div>
    )
  }

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

  const chartData = data.map(item => ({
    name: String(item.label || 'Unknown'),
    value: parseNumericValue(item.value),
    originalValue: item.value // Keep original for display
  }))

  const isMobile = window.innerWidth <= 768
  const chartHeight = dimensions.height

  const commonAxisStyle = {
    fontSize: isMobile ? 10 : 12,
    fill: '#d1d5db'
  }

  const commonTooltipStyle = {
    backgroundColor: '#1f2937',
    border: '2px solid #10b981',
    borderRadius: '8px',
    color: '#ffffff',
    fontSize: isMobile ? 11 : 13
  }
  console.log(chartData);
  console.log(type);
  const renderChart = () => {
    try {
      switch (type) {
        case 'bar':
          return (
            <ResponsiveContainer width="100%" height={chartHeight}>
              <BarChart 
                data={chartData} 
                margin={{ top: 20, right: 20, left: 0, bottom: 80 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#6b7280" />
                <XAxis 
                  dataKey="name" 
                  stroke="#d1d5db"
                  tick={commonAxisStyle}
                  angle={-45}
                  textAnchor="end"
                  height={90}
                  interval="preserveStartEnd"
                />
                <YAxis 
                  stroke="#d1d5db"
                  tick={commonAxisStyle}
                  width={50}
                />
                <Tooltip contentStyle={commonTooltipStyle} />
                <Legend 
                  wrapperStyle={{ fontSize: isMobile ? 11 : 13, paddingTop: 10, color: '#d1d5db' }} 
                />
                <Bar dataKey="value" fill="#10b981" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )

        case 'line':
          return (
            <ResponsiveContainer width="100%" height={chartHeight}>
              <LineChart 
                data={chartData}
                margin={{ top: 20, right: 20, left: 0, bottom: 80 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#6b7280" />
                <XAxis 
                  dataKey="name" 
                  stroke="#d1d5db"
                  tick={commonAxisStyle}
                  angle={-45}
                  textAnchor="end"
                  height={90}
                  interval="preserveStartEnd"
                />
                <YAxis 
                  stroke="#d1d5db"
                  tick={commonAxisStyle}
                  width={50}
                />
                <Tooltip contentStyle={commonTooltipStyle} />
                <Legend 
                  wrapperStyle={{ fontSize: isMobile ? 11 : 13, paddingTop: 10, color: '#d1d5db' }} 
                />
                <Line
                  type="monotone"
                  dataKey="value"
                  stroke="#10b981"
                  strokeWidth={3}
                  dot={{ fill: '#10b981', r: 5, stroke: '#10b981', strokeWidth: 2 }}
                  activeDot={{ r: 7, strokeWidth: 2 }}
                />
              </LineChart>
            </ResponsiveContainer>
          )

        case 'pie':
          return (
            <ResponsiveContainer width="100%" height={chartHeight}>
              <PieChart>
                <Pie
                  data={chartData}
                  cx="50%"
                  cy="45%"
                  labelLine={false}
                  label={!isMobile ? (entry) => entry.name : false}
                  outerRadius={isMobile ? 80 : 100}
                  fill="#8884d8"
                  dataKey="value"
                  stroke="#1f2937"
                  strokeWidth={2}
                >
                  {chartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip contentStyle={commonTooltipStyle} />
                <Legend 
                  wrapperStyle={{ fontSize: isMobile ? 10 : 12, color: '#d1d5db' }} 
                  verticalAlign="bottom"
                />
              </PieChart>
            </ResponsiveContainer>
          )

        case 'scatter':
          return (
            <ResponsiveContainer width="100%" height={chartHeight}>
              <ScatterChart margin={{ top: 20, right: 20, left: 0, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#6b7280" />
                <XAxis 
                  dataKey="name" 
                  stroke="#d1d5db"
                  tick={commonAxisStyle}
                />
                <YAxis 
                  dataKey="value" 
                  stroke="#d1d5db"
                  tick={commonAxisStyle}
                  width={40}
                />
                <Tooltip contentStyle={commonTooltipStyle} />
                <Legend 
                  wrapperStyle={{ fontSize: isMobile ? 11 : 13, paddingTop: 10, color: '#d1d5db' }} 
                />
                <Scatter 
                  name="Data" 
                  data={chartData} 
                  fill="#10b981"
                />
              </ScatterChart>
            </ResponsiveContainer>
          )

        default:
          return <div className="chart-error">Unsupported chart type: {type}</div>
      }
    } catch (error) {
      console.error('Chart rendering error:', error)
      return <div className="chart-error">Error: {error.message}</div>
    }
  }

  return (
    <div className="chart-container" ref={containerRef} style={{ minHeight: chartHeight + 60 }}>
      {renderChart()}
    </div>
  )
}

export default ChartView
