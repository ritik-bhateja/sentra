# Requirements Document

## Introduction

This specification defines the requirements for updating the insurance database schema documentation in the Sentra banking chatbot system. The insurance database has been restructured from a two-table model (INSURANCE_POLICIES and INSURANCE_CLAIMS) to a single consolidated table (INSURANCE_DATA) containing comprehensive policy information with over 100 columns. The system prompt must be updated to reflect this new schema structure to ensure accurate SQL query generation for insurance-related queries.

## Glossary

- **System**: The Sentra banking AI chatbot application
- **Agent Prompt**: The system prompt provided to the AWS Bedrock agent that guides SQL query generation
- **insurance_db**: The AWS Athena database containing insurance data (separate from sentra_db)
- **INSURANCE_DATA**: The new consolidated table in insurance_db containing all policy information
- **prompt.py**: The Python module containing all agent prompt definitions
- **insurance_schema_prompt**: The specific prompt section documenting the insurance database schema

## Requirements

### Requirement 1

**User Story:** As a developer maintaining the Sentra chatbot, I want the insurance schema documentation updated in prompt.py, so that the AI agent can generate accurate SQL queries against the new INSURANCE_DATA table structure.

#### Acceptance Criteria

1. WHEN the insurance_schema_prompt is updated THEN the System SHALL remove all references to the INSURANCE_POLICIES table
2. WHEN the insurance_schema_prompt is updated THEN the System SHALL remove all references to the INSURANCE_CLAIMS table
3. WHEN the insurance_schema_prompt is updated THEN the System SHALL document the INSURANCE_DATA table as the single table in insurance_db
4. WHEN the insurance_schema_prompt is updated THEN the System SHALL include all column names from the INSURANCE_DATA table with their data types
5. WHEN the insurance_schema_prompt is updated THEN the System SHALL preserve all existing rules about database selection (database="insurance_db")
6. WHEN the insurance_schema_prompt is updated THEN the System SHALL preserve all existing rules about no access restrictions on insurance data
7. WHEN the insurance_schema_prompt is updated THEN the System SHALL update example queries to reference INSURANCE_DATA instead of INSURANCE_POLICIES or INSURANCE_CLAIMS
8. WHEN the base_prompt references insurance tables THEN the System SHALL update those references to mention only INSURANCE_DATA
9. WHEN the System processes insurance queries THEN the System SHALL maintain the existing behavior of routing to insurance_db database
10. WHEN the schema update is complete THEN the System SHALL not modify any sentra_db schema documentation

### Requirement 2

**User Story:** As a user of the Sentra chatbot, I want query results to be displayed as charts and graphs when appropriate, so that I can quickly understand data patterns and trends visually.

#### Acceptance Criteria

1. WHEN a query contains GROUP BY clause THEN the System SHALL prefer to return results in pictorial format (bar, line, pie, or scatter chart)
2. WHEN query results contain categorical aggregations THEN the System SHALL use chart type "bar" or "pie" for the response
3. WHEN query results contain time-series data THEN the System SHALL use chart type "line" for the response
4. WHEN query results contain correlation data THEN the System SHALL use chart type "scatter" for the response
5. WHEN the agent formats chart responses THEN the System SHALL include the data array with label-value pairs as specified in the response format
