# Row-Level Security Implementation

## Overview

Implemented code-based row-level security for insurance_db queries using hierarchical access control based on user_data.user_data table.

## Architecture

```
Frontend (user_email) 
    ↓
BackendAPI/Agent_Trigger.py (FastAPI)
    ↓
Backend/main.py (Bedrock AgentCore entrypoint)
    ↓
Backend/agent/sql_agent.py (SQLQueryExecutor with user_email in state)
    ↓
Backend/tools/athena_query.py (Tool with security filter)
    ↓
Backend/tools/query_security.py (QuerySecurityFilter - SQL injection)
    ↓
AWS Athena (Executes filtered query)
```

## Key Components

### 1. QuerySecurityFilter (Backend/tools/query_security.py)
- **Purpose**: Inject WHERE clause into SQL queries for insurance_db
- **Method**: `inject_security_filter(sql, user_email, database)`
- **Logic**: 
  ```sql
  WHERE email IN (
      SELECT reportee_email 
      FROM user_data.user_data 
      WHERE self_email = 'user@sentra.com'
  )
  ```
- **Features**:
  - Only applies to insurance_db (not sentra_db)
  - Handles existing WHERE clauses (adds AND condition)
  - Handles queries without WHERE (adds new WHERE)
  - Preserves GROUP BY, ORDER BY, LIMIT, HAVING clauses
  - Email validation to prevent SQL injection

### 2. Modified athena_query Tool (Backend/tools/athena_query.py)
- Added `user_email` parameter to tool schema
- Calls `QuerySecurityFilter.inject_security_filter()` before query execution
- Validates email format
- Logs original and modified SQL

### 3. Secure Tool Wrapper (Backend/agent/sql_agent.py)
- `create_secure_athena_query()` function wraps athena_query
- Automatically extracts `user_email` from agent state
- Injects it into every tool call
- **Prevents prompt injection** - LLM cannot bypass security

### 4. SQLQueryExecutor Updates (Backend/agent/sql_agent.py)
- Constructor accepts `user_email` parameter
- Stores `user_email` in agent state
- Creates secure wrapper for athena_query tool

### 5. Entrypoint Updates (Backend/main.py)
- Extracts `user_email` from payload
- Passes to SQLQueryExecutor constructor
- Fallback to `user_id` if email not provided

### 6. API Updates (BackendAPI/Agent_Trigger.py)
- Added `user_email` field to QueryRequest model (optional)
- Includes `user_email` in Bedrock AgentCore payload
- Fallback to `user_id` if not provided

## Security Features

### 1. Code-Based Enforcement
- Security filter applied at **code level**, not prompt level
- LLM cannot bypass or modify the filter
- Immune to prompt injection attacks

### 2. SQL Injection Prevention
- Email validation with regex pattern
- Checks for dangerous SQL keywords (DROP, DELETE, UPDATE, etc.)
- Rejects invalid email formats

### 3. Database-Specific
- Only applies to `insurance_db`
- Other databases (sentra_db) unaffected
- Configurable per database

### 4. Hierarchical Access
- Uses user_data.user_data table for hierarchy
- super.admin sees all reportees
- Managers see their team
- Agents see only their own data

## User Hierarchy (from USER_DATA.csv)

```
super.admin@sentra.com
├── super.admin@sentra.com (self)
├── kamaljeet.singh@sentra.com
├── vishal.saxena@sentra.com
└── harsh.kumar@sentra.com

kamaljeet.singh@sentra.com
├── kamaljeet.singh@sentra.com (self)
├── vishal.saxena@sentra.com
└── harsh.kumar@sentra.com

vishal.saxena@sentra.com
├── vishal.saxena@sentra.com (self)
└── harsh.kumar@sentra.com

harsh.kumar@sentra.com
└── harsh.kumar@sentra.com (self)
```

## Example Query Transformations

### Example 1: Simple SELECT
**Original:**
```sql
SELECT * FROM insurance_data
```

**Modified (for harsh.kumar@sentra.com):**
```sql
SELECT * FROM insurance_data 
WHERE email IN (
    SELECT reportee_email 
    FROM user_data.user_data 
    WHERE self_email = 'harsh.kumar@sentra.com'
)
```

### Example 2: SELECT with WHERE
**Original:**
```sql
SELECT * FROM insurance_data WHERE policy_type = 'Health'
```

**Modified (for vishal.saxena@sentra.com):**
```sql
SELECT * FROM insurance_data 
WHERE (policy_type = 'Health') AND email IN (
    SELECT reportee_email 
    FROM user_data.user_data 
    WHERE self_email = 'vishal.saxena@sentra.com'
)
```

### Example 3: SELECT with GROUP BY
**Original:**
```sql
SELECT policy_type, COUNT(*) FROM insurance_data GROUP BY policy_type
```

**Modified (for kamaljeet.singh@sentra.com):**
```sql
SELECT policy_type, COUNT(*) FROM insurance_data 
WHERE email IN (
    SELECT reportee_email 
    FROM user_data.user_data 
    WHERE self_email = 'kamaljeet.singh@sentra.com'
) 
GROUP BY policy_type
```

## Testing

Run the test script:
```bash
cd Backend/tools
python test_security_filter.py
```

Tests cover:
- Simple SELECT without WHERE
- SELECT with existing WHERE
- SELECT with GROUP BY
- SELECT with ORDER BY and LIMIT
- Non-insurance database (should not modify)
- Email validation (valid and invalid formats)
- SQL injection attempts

## Frontend Integration

Update frontend to send user_email:
```javascript
const response = await fetch('http://localhost:5000/query', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        user_query: query,
        user_id: userId,
        session_id: sessionId,
        user_email: userEmail  // Add this field
    })
});
```

## Benefits

1. **Security**: Code-based enforcement prevents bypass
2. **Transparency**: All queries logged with original and modified SQL
3. **Flexibility**: Easy to modify hierarchy in user_data table
4. **Performance**: Single subquery added to each query
5. **Maintainability**: Centralized security logic in one module
6. **Auditability**: Full logging of security filter application

## Limitations

1. Requires user_data.user_data table in Athena
2. Adds subquery overhead to every insurance_db query
3. Email must be present in insurance_data table
4. Only works for insurance_db (by design)

## Future Enhancements

1. Cache user hierarchy to reduce subquery overhead
2. Support multiple security models (role-based, attribute-based)
3. Add audit logging for security violations
4. Support complex hierarchies (multi-level reporting)
5. Add performance monitoring for filtered queries
