# Implementation Plan

- [x] 1. Prepare column list with data types from CSV
  - Extract all 142 column names from insurance_synthetic_data.csv header
  - Analyze sample data to determine appropriate data type for each column
  - Create formatted list in the style: `column_name (DATA_TYPE)`
  - _Requirements: 1.4_

- [x] 2. Update insurance_schema_prompt in prompt.py
  - [x] 2.1 Replace entire insurance_schema_prompt variable with new documentation
    - Remove all references to INSURANCE_POLICIES table
    - Remove all references to INSURANCE_CLAIMS table
    - Document INSURANCE_DATA as the single table in insurance_db
    - Include all 142 columns with their data types
    - Preserve database selection rules (database="insurance_db")
    - Preserve no access restrictions rule
    - Update all SQL example queries to use INSURANCE_DATA
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7_

- [x] 3. Update base_prompt in prompt.py
  - [x] 3.1 Update table references in Step 3 section
    - Change "insurance_db has: INSURANCE_POLICIES, INSURANCE_CLAIMS" to "insurance_db has: INSURANCE_DATA"
    - Update example queries to reference INSURANCE_DATA
    - _Requirements: 1.8_

  - [x] 3.2 Update database description section
    - Change "Contains: INSURANCE_POLICICIES, INSURANCE_CLAIMS" to "Contains: INSURANCE_DATA"
    - _Requirements: 1.8_

- [x] 4. Verify banking schema unchanged
  - [x] 4.1 Compare customer_schema_prompt before and after changes
    - Ensure customer_schema_prompt variable is not modified
    - Verify all sentra_db table documentation remains identical
    - _Requirements: 1.10_

- [x] 5. Final validation
  - Manually review the updated prompt for formatting and clarity
  - Verify all old table references are removed
  - Verify all columns from CSV are documented
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.10_

- [x] 6. Add chart visualization preference instructions
  - [x] 6.1 Update RESPONSE FORMAT section in base_prompt
    - Add visualization preference rule emphasizing chart format for GROUP BY queries
    - Add chart type selection guidelines (bar for categorical, line for time-series, pie for distributions, scatter for correlations)
    - Clarify that text format should only be used for single aggregate values
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_
