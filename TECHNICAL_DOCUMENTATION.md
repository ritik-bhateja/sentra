# Sentra Insurance AI Chatbot - Technical Documentation

## Table of Contents
1. System Overview
2. Architecture
3. Backend Components
4. Frontend Components
5. Database Schema
6. API Endpoints
7. Deployment
8. Security & Access Control
9. Memory Management
10. Testing
11. Configuration
12. Development Workflow

## System Overview

**Sentra** is an AI-powered conversational interface for insurance data analysis. The system enables users to query complex insurance datasets using natural language, automatically generating SQL queries and returning results in both textual and visual formats.

### Key Features
- Natural language to SQL query generation
- Insurance data analysis and insights
- Interactive chart visualizations
- Performance insights with Nudge and CTA (Call-to-Action) for insurance data
- Conversation memory with session isolation
- Real-time query execution via AWS Athena

### Technology Stack
- **Backend**: Python 3.10, Flask, AWS Bedrock Agent Core, Strands Agent Framework
- **Frontend**: React 18, Vite, Recharts
- **AI Model**: Claude Sonnet 4 (apac.anthropic.claude-sonnet-4-20250514-v1:0)
- **Database**: AWS Athena (insurance_db)
- **Infrastructure**: AWS (Bedrock, S3, IAM, ECR, CodeBuild, Glue)

### AWS Services Used
- **AWS Bedrock Agent Core**: AI agent runtime and orchestration
- **AWS Bedrock Memory**: Conversation storage and session management
- **AWS Athena**: SQL query engine for data analysis
- **AWS S3**: Source code storage, query results, and data lake storage
- **AWS Glue**: Data catalog and schema management for Parquet files
- **AWS CodeBuild**: CI/CD pipeline for containerized deployments
- **Amazon ECR**: Container registry for Docker images
- **AWS IAM**: Identity and access management for service permissions

## Architecture

### High-Level Architecture
```
┌─────────────────────────────────────────────────────────────────┐
│                    FRONTEND (React + Vite)                      │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐    │
│  │  ChatInterface  │ │   ChartView     │ │  CustomerList   │    │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘    │
└────────────────────┬────────────────────────────────────────────┘
                     │ HTTP POST /query
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FLASK API LAYER                              │
│  ┌─────────────────┐                                            │
│  │  Agent_Trigger  │                                            │
│  │     .py         │                                            │
│  └─────────────────┘                                            │
└────────────────────┬────────────────────────────────────────────┘
                     │ boto3.client('bedrock-agentcore')
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                BEDROCK AGENTCORE RUNTIME                        │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐    │
│  │     main.py     │ │  sql_agent.py   │ │  memory_hook.py │    │
│  │  (entrypoint)   │ │ (SQLExecutor)   │ │   (memory)      │    │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘    │
└────────────────────┬────────────────────────────────────────────┘
                     │ athena_query tool
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                      AWS ATHENA                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  insurance_db (Insurance) - 1 table                      │   │
│  │  - INSURANCE_DATA (142 columns)                          │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### Request Flow
1. **User Input**: Natural language query via React frontend
2. **API Gateway**: Flask server receives POST request with user_query, user_id, session_id
3. **Agent Runtime**: Bedrock Agent Core invokes main.py entrypoint
4. **SQL Generation**: Strands Agent with Claude Sonnet 4 generates SQL
5. **Database Query**: athena_query tool executes SQL on insurance_db database
6. **Response Processing**: Results formatted as JSON with charts/text
7. **Memory Storage**: Conversation stored in Bedrock Memory
8. **UI Rendering**: Frontend displays results with Recharts visualizations

## AWS Infrastructure

### Core AWS Services Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      AWS INFRASTRUCTURE                         │
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────┐  │
│  │   CodeBuild     │    │      ECR        │    │     S3      │  │
│  │   Project       │───▶│   Repository    │    │   Buckets   │  │
│  │                 │    │                 │    │             │  │
│  └─────────────────┘    └─────────────────┘    └─────────────┘  │
│           │                       │                     │       │
│           │                       ▼                     │       │
│           │              ┌─────────────────┐            │       │
│           │              │ Bedrock Agent   │            │       │
│           └─────────────▶│ Core Runtime    │◀───────────┘       │
│                          │                 │                    │
│                          └─────────────────┘                    │
│                                   │                             │
│                                   ▼                             │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────┐  │
│  │   IAM Roles     │    │     Athena      │    │    Glue     │  │
│  │ & Policies      │    │   Workgroup     │    │  Catalog    │  │
│  │                 │    │                 │    │             │  │
│  └─────────────────┘    └─────────────────┘    └─────────────┘  │
│                                   │                     │       │
│                                   ▼                     ▼       │
│                          ┌─────────────────────────────────────┐│
│                          │        S3 Data Lake                 ││
│                          │     (Parquet Files)                 ││
│                          └─────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

### S3 Buckets

#### 1. Source Code Bucket
**Purpose**: Stores source code for CodeBuild deployments
**Contents**:
- Backend Python application code
- Requirements and dependency files

**Usage**:
- CodeBuild pulls source code from this bucket
- Automated deployments trigger from code updates

#### 2. Query Output Bucket
**Purpose**: Stores Athena query results and execution metadata
**Structure**:
```
s3://bedrock-agentcore-runtime-{region}/
└── QueryOutput/
        ├── results.csv
        └── metadata.json

```

**Features**:
- Structured storage by execution ID
- CSV format for easy data processing
- Metadata tracking for query performance

#### 3. Data Lake Bucket
**Purpose**: Stores insurance data in Parquet format
**Structure**:
```
s3://bedrock-agentcore-runtime-{region}/
└── INSURANCE_DATA/
    └── INSURANCE_DATA/
        └── data.parquet
```

**Features**:
- **Storage Format**: Parquet format for optimal query performance
- **Compression**: Snappy compression for balance between size and query speed

### Amazon ECR Repository

**Purpose**: Container registry for Docker images
**Repository Structure**:
```
ECR Repository: sentra-backend
├── Image Tags:
│   ├── 1
│   ├── 2
│   ├── 3
│   └── latest (current deployment)
```

**Features**:
- **Automated Builds**: CodeBuild pushes images after successful builds
- **Image Scanning**: Vulnerability scanning enabled for security
- **Lifecycle Policies**: Automatic cleanup of old images

**Image Configuration**:
- **Base Image**: aws/codebuild/amazonlinux2-aarch64-standard:3.0
- **Size Optimization**: Multi-stage builds to minimize image size
- **Security**: Non-root user execution

### AWS CodeBuild Project

**Purpose**: CI/CD pipeline for automated deployments
**Project Configuration**:

**Build Environment**:
- **Compute Type**: BUILD_GENERAL1_MEDIUM (4 vCPU, 7 GB memory)
- **Operating System**: Amazon Linux 2
- **Runtime**: Standard:3.0

**Build Specification**: Uses buildspec.yml file included in the codebase

**Triggers**:
- **Manual**: Triggered via Agent_CICD.py script


### IAM Roles and Policies

#### Key IAM Roles
- **AmazonBedrockAgentCoreSDKCodeBuild**: CodeBuild service role for container builds and deployments
- **AmazonBedrockAgentCoreSDKRuntime**: Runtime execution role for Bedrock Agent Core operations

**Role Functions**:
- **CodeBuild Role**: Enables building, pushing to ECR, and deploying containers
- **Runtime Role**: Allows Bedrock Agent Core to access Athena, S3, and other AWS services

### AWS Athena Configuration

#### Database Structure
```sql
-- Insurance Database
CREATE DATABASE insurance_db
LOCATION 's3://bedrock-agentcore-runtime-{region}/INSURANCE_DATA/'
```

### AWS Glue Data Catalog

#### Purpose
- **Schema Management**: Centralized metadata store for all tables
- **Data Discovery**: Automatic schema detection from Parquet files
- **Data Lineage**: Track data transformations and dependencies

#### Catalog Structure
```
Glue Data Catalog
├── Databases:
    ├── insurance_db
       └── Tables:
           └── insurance_data (142 columns)

```
#### Table Properties
**Insurance Data Table**:
- **Storage Format**: Parquet
- **Compression**: Snappy

### Data Pipeline Architecture

#### ETL Process Flow
```
Source Systems → S3 Raw Data → Glue ETL → S3 Processed (Parquet) → Glue Catalog → Athena
```

1. **Data Ingestion**: Raw data uploaded to S3 staging area
2. **ETL Processing**: Glue jobs convert to Parquet format
3. **Catalog Update**: Crawler updates table schemas
4. **Query Access**: Athena queries optimized Parquet data



### Core Files Structure
```
Backend/
├── main.py                    # Bedrock Agent Core entrypoint
├── Agent_Trigger.py           # Flask API server
├── Agent_CICD.py             # Deployment configuration
├── requirements.txt          # Python dependencies
├── agent/
│   ├── sql_agent.py         # SQLQueryExecutor class
│   └── prompt.py            # System prompts (base, insurance)
├── tools/
│   ├── athena_query.py      # AWS Athena query tool
│   └── knowledge_base_retrieve.py
├── memory/
│   ├── memory_setup.py      # Memory client initialization
│   └── memory_hook.py       # Conversation memory hooks
├── config/
│   └── logger.py            # Logging configuration
└── tests/
    ├── test_schema_integrity.py
    └── validate_final_prompt.py

```
### 1. main.py - Agent Entrypoint
**Purpose**: Entry point for Bedrock Agent Core runtime
**Key Functions**:
- Validates user_id and session_id from payload
- Sanitizes actor_id for AWS Bedrock Memory compatibility
- Initializes SQLQueryExecutor with session isolation
- Handles exceptions and returns standardized JSON responses

```python
@app.entrypoint
def main(payload, context = None):
    # Extract and validate identifiers
    user_id = payload.get("user_id")
    session_id = payload.get("session_id")
    
    # Sanitize for AWS Bedrock Memory
    actor_id = user_id.replace('.', '_').replace('@', '_at_')
    
    # Initialize SQL executor with session isolation
    generator = SQLQueryExecutor(actor_id=actor_id, session_id=session_id)
    return generator.execute_sql(payload.get("user_query", ""), user_id)
```

### 2. Agent_Trigger.py - Flask API Server
**Purpose**: HTTP API layer with CORS support
**Endpoints**:
- `POST /query`: Main chatbot endpoint → Bedrock Agent Core
- `POST /users`: Direct Athena query for customer list

**Key Features**:
- CORS enabled for all origins
- Session ID validation (33-character requirement)
- Direct Athena integration for customer data

### 3. sql_agent.py - SQL Query Executor
**Purpose**: Core AI agent for SQL generation and execution
**Components**:
- **BedrockModel**: Claude Sonnet 4 integration
- **Strands Agent**: AI framework with tools and memory
- **System Prompts**: Insurance schema knowledge
- **JSON Response Parsing**: Extracts structured responses

**Key Methods**:
```python
class SQLQueryExecutor:
    def __init__(self, actor_id, session_id, region='ap-south-1', 
                 model_id='apac.anthropic.claude-sonnet-4-20250514-v1:0')
    def execute_sql(self, user_query, user_id)
```

### 4. prompt.py - System Prompts
**Purpose**: Contains all AI prompts and database schemas
**Components**:
- **base_prompt**: Core instructions, response formats, security rules
- **insurance_schema_prompt**: Insurance database schema (insurance_db)

**Key Features**:
- Database selection rules for insurance queries
- Response format specifications (text, bar, line, pie, scatter)
- Security rules (never expose technical details)

### 5. athena_query.py - Database Tool
**Purpose**: Strands tool for AWS Athena query execution
**Parameters**:
- `sql`: SQL query string
- `database`: Required - "insurance_db"
- `workgroup`: Athena workgroup (default: "primary")
- `output_s3`: S3 location for query results

**Features**:
- Automatic query polling until completion
- Error handling and logging
- Result parsing to Python dictionaries

### 6. Memory System
**Components**:
- **memory_setup.py**: Initializes Bedrock Memory client
- **memory_hook.py**: Handles conversation storage/retrieval

**Memory Features**:
- Session-based isolation (actor_id + session_id)
- Loads last 5 conversation turns on agent initialization
- Stores messages after each interaction
- 7-day event expiry

## Frontend Components

### Core Structure
```
Frontend/src/
├── App.jsx                   # Main application component
├── components/
│   ├── ChatInterface.jsx     # Main chat UI
│   ├── ChatMessage.jsx       # Message rendering
│   ├── ChartView.jsx         # Chart visualizations
│   ├── CustomerList.jsx      # Customer list view
│   ├── CustomerCard.jsx      # Customer profile cards
│   ├── Login.jsx             # Authentication
│   ├── Sidebar.jsx           # Navigation sidebar
│   └── UserProfile.jsx       # User profile display
├── utils/
└── main.jsx                  # React entry point
```

### Key Components

#### 1. ChatInterface.jsx
**Purpose**: Main chat interface with session management
**Features**:
- Session creation with 33-character IDs (AWS requirement)
- Message history persistence in localStorage
- Real-time API communication with abort capability
- Chart rendering integration

#### 2. ChartView.jsx
**Purpose**: Data visualization using Recharts
**Supported Chart Types**:
- **Bar Charts**: Categorical comparisons
- **Line Charts**: Time-series trends
- **Pie Charts**: Percentage distributions
- **Scatter Plots**: Correlations

#### 3. CustomerList.jsx
**Purpose**: Customer data display with search/filter
**Features**:
- Direct Athena query via `/users` endpoint
- Customer profile integration

### Session Management
- **Session ID Format**: `{timestamp}_{19-char-random}` (33 chars total)
- **Storage**: localStorage per user
- **Structure**: `sentra_sessions_{userId}`

## Database Schema

### Insurance Database (insurance_db)
**1 Consolidated Table**:

**INSURANCE_DATA** (142 columns)
- Policy information (28 columns)
- Customer information (13 columns)
- Agent information (15 columns)
- Transaction information (18 columns)
- Branch information (8 columns)
- Benefit groups (20 columns)
- Tax information (4 columns)
- Status and processing (10 columns)

## API Endpoints

### POST /query
**Purpose**: Main chatbot interaction endpoint
**Request**:
```json
{
  "user_query": "Show me top 10 customers by balance",
  "user_id": "user.name",
  "session_id": "1767339643424_xIZ6cGPIIoxYKP3IdcN"
}
```

**Response Formats**:

1. **Text Response**:
```json
{
  "type": "text",
  "data": "123",
  "explanation": "Found 123 active policies",
  "customer_specific": "False",
  "query_executed": "SELECT COUNT(*) FROM insurance_data"
}
```

2. **Chart Response**:
```json
{
  "type": "bar",
  "data": [
    {"label": "Q1", "value": "45000"},
    {"label": "Q2", "value": "52000"}
  ],
  "explanation": "Quarterly sales performance",
  "customer_specific": "False",
  "query_executed": "SELECT quarter, SUM(amount) FROM sales GROUP BY quarter"
}
```

### 3. Insurance Response with Performance Insights

**Type:**  
`bar`

**Data:**
- Agent A → ₹45,000  
- Agent B → ₹32,000  

**Explanation:**  
Agent performance analysis

**Customer Specific:**  
False

**Query Executed:**  
`SELECT agent_name, SUM(gwp) FROM insurance_data GROUP BY agent_name`

**Nudge (Performance Insight):**  
> **1. Performance Gap (Agent B)**  
> Agent B shows a **29% performance gap** compared to average.  
>  
> **The Issue:**  
> Only ₹32,000 vs ₹45,000 average premium.  
>  
> **Root Cause:**  
> Focus on low-premium Individual policies instead of higher-value Group policies.

**CTA (Call to Action):**
> **Action 1: Agent B — Product Mix Training**  
> **Priority:** HIGH  
> **Execution:** 30-day Group policy certification program  
> **Target:**  
> 40% Group policy mix, ₹13,000 premium increase (41% boost)


## Performance Insights (Insurance Data Only)

### Nudge - Performance Analysis
**Purpose**: Provides fact-based analysis of underperforming entities in insurance queries
**Features**:
- **Automatic Detection**: Triggered for insurance queries with GROUP BY operations
- **Data-Driven**: Based on actual database metrics and comparisons
- **Structured Format**: Numbered sections with specific performance gaps
- **Entity Coverage**: 1-4 lowest performing entities based on result count

**Nudge Structure**:
```
**[Number]. [Category] ([Entity Name])**
[Entity] shows a [X]% performance gap compared to [benchmark].

**The Issue:** [Specific metric comparison with numbers]
**Root Cause:** [Data-driven analysis of why this is happening]
```

### CTA - Call to Action
**Purpose**: Provides specific, actionable recommendations for underperforming entities
**Features**:
- **Action-Oriented**: Concrete steps to improve performance
- **Prioritized**: HIGH/MEDIUM/LOW priority levels
- **Measurable Targets**: Specific goals with numbers and timelines
- **Entity-Specific**: Tailored actions for each underperforming entity

**CTA Structure**:
```
Action [Number]: [Entity Name] — [Action Type]
Priority: [HIGH/MEDIUM/LOW]
Execution: [Concise single-line action]
Target: [Detailed measurable outcome with context]
```

### When Nudge & CTA Are Included
**Always Included For**:
- Generalized insurance queries (no LIMIT clause)
- Filtered insurance queries (specific parameters but no LIMIT)
- "Least performing" queries (bottom, worst, minimum, etc.)
- "Top X" queries where actual results < requested limit

**Never Included For**:
- "Top X" queries where results >= requested limit
- Single value queries (COUNT, SUM without GROUP BY)
```

### POST /users
**Purpose**: Direct customer list retrieval
**Request**:
```json
{
  "user_id": "user.name"
}
```

**Response**:
```json
{
  "status": "ok",
  "execution_id": "query-execution-id",
  "rows": [
    {
      "CIF_NO": "CIF200001",
      "CUSTOMER_NAME": "John Doe",
      "MOBILE_PHONE": "9876543210",
      "EMAIL_ADDRESS": "john@example.com"
    }
  ]
}
```

## Deployment

### Deployment Methods

#### Container Deployment
```bash
cd Backend
python Agent_CICD.py
```

**Process**:
- CodeBuild builds Docker container
- Pushes to ECR repository
- Deploys to Bedrock Agent Core Runtime

### Configuration Files
- **requirements.txt**: Python dependencies

## Security & Access Control

### Security Rules
- **Never expose technical details**: Database names, table names, SQL queries hidden from users
- **Business-friendly language**: All user-facing messages use business terminology
- **Input validation**: user_id and session_id required for all requests
- **Memory isolation**: Conversations isolated by actor_id + session_id

## Memory Management

### Bedrock Memory Integration
- **Memory Name**: "Sentra_Agent_Memory_V1"
- **Event Expiry**: 7 days
- **Session Isolation**: actor_id + session_id combination

### Memory Hooks
1. **Agent Initialization**: Loads last 5 conversation turns
2. **Message Storage**: Saves each user/assistant interaction
3. **Context Loading**: Adds conversation history to system prompt

### Memory Client Configuration
```python
client = MemoryClient(region_name="ap-south-1")
memory = client.create_memory_and_wait(
    name="Sentra_Agent_Memory_V1",
    strategies=[],
    description="Short-term memory for Sentra agent",
    event_expiry_days=7
)
```

## Testing

### Test Files
- **test_schema_integrity.py**: Validates insurance schema documentation
- **validate_final_prompt.py**: Ensures prompt consistency
- **test_memory.py**: Memory functionality tests
- **test_user_isolation.py**: User isolation validation

### Test Categories
1. **Schema Integrity**: Verifies database schema documentation
2. **Access Control**: Tests user access validation
3. **Memory Isolation**: Validates session separation
4. **Prompt Validation**: Ensures AI prompt consistency

### Running Tests
```bash
cd Backend
python tests/test_schema_integrity.py
python tests/validate_final_prompt.py
```

## Configuration

### Environment Variables
**Backend**:
```bash
AWS_REGION=ap-south-1
AWS_ACCESS_KEY_ID=<your-key>
AWS_SECRET_ACCESS_KEY=<your-secret>
```

**Frontend**:
```bash
VITE_API_URL=http://localhost:5000
```

### Model Configuration
**Current Model**: Claude Sonnet 4
```python
model_id='apac.anthropic.claude-sonnet-4-20250514-v1:0'
region='ap-south-1'
```

### Database Configuration
```python
DATABASE_INSURANCE = "insurance_db"
```

## Development Workflow

### Backend Development
1. **Setup Environment**:
   ```bash
   cd Backend
   python -m venv aws_env
   source aws_env/bin/activate  # Linux/Mac
   pip install -r requirements.txt
   ```

2. **Local Testing**:
   ```bash
   python Agent_Trigger.py  # Starts Flask on port 5000
   ```

3. **Deployment**:
   ```bash
   python Agent_CICD.py  # Deploys to AWS
   ```

### Frontend Development
1. **Setup**:
   ```bash
   cd Frontend
   npm install
   ```

2. **Development Server**:
   ```bash
   npm run dev  # Starts Vite on port 5173
   ```

3. **Build**:
   ```bash
   npm run build
   ```

### Common Development Tasks

#### Adding New Database Tables
1. Update `insurance_schema_prompt` in `prompt.py`
2. Add table schema with column names and data types
3. Include example queries
4. Test with `test_schema_integrity.py`

#### Modifying Response Formats
1. Update `base_prompt` RESPONSE FORMAT section
2. Modify frontend `ChatMessage.jsx` to handle new format
3. Update `ChartView.jsx` for new chart types
4. Test end-to-end functionality

#### Adding New User Roles
1. Update `base_prompt` PERSONA ACCESS RULES
2. Define CIF_NO range for new user
3. Add user to frontend `Login.jsx` dropdown
4. Test access control with `test_user_isolation.py`

### Troubleshooting

#### Common Issues
1. **Agent Returns Wrong Database**: Check database selection rules in prompt
2. **Charts Not Rendering**: Verify response type and data format
3. **Memory Not Persisting**: Verify actor_id and session_id format

#### Debugging Tools
- **Backend Logs**: Check CloudWatch logs for agent runtime
- **Frontend Console**: Browser developer tools for API errors
- **Athena Console**: Query execution history and errors
- **Memory Console**: Bedrock Memory event history

### Performance Optimization
- **Query Optimization**: Use appropriate WHERE clauses and indexes
- **Memory Management**: Limit conversation history to 5 turns
- **Response Caching**: Consider caching frequent queries
- **Chart Data**: Limit data points for better rendering performance

---

## Conclusion

The Sentra Insurance AI Chatbot represents a sophisticated integration of modern AI technologies with enterprise insurance data systems. The architecture provides scalable, secure, and user-friendly access to complex insurance datasets while maintaining conversation context and providing actionable business insights.

The system's modular design allows for easy extension to additional databases, new chart types, and enhanced AI capabilities while maintaining security and performance standards required for insurance applications.