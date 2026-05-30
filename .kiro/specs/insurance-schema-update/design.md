# Design Document

## Overview

This design outlines the approach for updating the insurance database schema documentation in the `Backend/agent/prompt.py` file. The update involves:

1. Replacing references to the deprecated two-table structure (INSURANCE_POLICIES and INSURANCE_CLAIMS) with the new consolidated INSURANCE_DATA table that contains 142 columns covering all policy, customer, agent, and transaction information.

2. Adding visualization preference instructions to ensure the AI agent returns chart-based responses (bar, line, pie, scatter) for GROUP BY queries and aggregated data, improving data comprehension through visual representations.

## Architecture

The system uses a prompt-based architecture where the AWS Bedrock agent receives structured prompts that include:
1. Base instructions for query routing
2. Banking database schema (sentra_db) 
3. Insurance database schema (insurance_db)

The insurance schema prompt is a standalone string variable that gets concatenated with other prompts before being sent to the agent. This modular design allows us to update the insurance schema independently without affecting banking schema documentation.

## Components and Interfaces

### Modified Component

**File**: `Backend/agent/prompt.py`

**Variables to Update**:
- `insurance_schema_prompt` (string) - Complete replacement of schema documentation
- `base_prompt` (string) - Update table references in Step 3 and database description sections, add visualization preference rules in RESPONSE FORMAT section

**Interface**: These are Python string variables that are imported and used by `Backend/agent/sql_agent.py` in the SQLQueryExecutor class initialization.

### Visualization Preference Design

**Response Format Enhancement**:
The base_prompt will be updated to include explicit instructions for preferring chart visualizations over text responses when appropriate. This ensures better user experience by presenting data visually.

**Chart Type Selection Logic**:
- **Bar charts**: For categorical comparisons (e.g., policy count by type, premium by agent, policies by zone)
- **Pie charts**: For percentage distributions and market share analysis (e.g., business type breakdown)
- **Line charts**: For time-series data and trends (e.g., monthly policy counts, quarterly revenue)
- **Scatter charts**: For correlation analysis (e.g., premium vs sum insured, age vs premium)

**Decision Rule**:
- If query contains `GROUP BY` → Prefer chart format
- If query returns single aggregate value (COUNT, SUM, AVG without grouping) → Use text format
- If query returns multiple rows with aggregations → Use chart format

## Data Models

### New INSURANCE_DATA Table Structure

The INSURANCE_DATA table consolidates all insurance information into a single table with 142 columns organized into logical groups:

**Policy Information** (28 columns):
- policy_number, proposal_number, policy_type, policy_status_code
- risk_start_date, policy_end_date, date_of_issuance
- main_product, product, sub_package, sub_package_code, max_package_code
- business_type, sub_business_type, cover_type
- sum_insured, gwp, total_gwp, initial_premium, upsell_amnt
- rn_amount, initial_nol, nol, tenure
- master_policy_number, portability_type
- auto_renewal_flag, smartselect_flag, propero_y_flag

**Customer Information** (13 columns):
- customer_id, customer_name, customer_type, customer_zone
- customer_gender, customer_dob, customer_occupation
- customer_city, customer_pin_code, customer_address
- customer_contact_no, emailid, customer_pan

**Agent Information** (15 columns):
- agent_id, agent_name, agent_category, agent_state, agent_joining_date
- rm_id, rm_sm_name, latest_rm_id, latest_rm_nm
- partner_rm_code, parent_bp_name, parent_bp_code
- intermediary_category, vertical, sub_vertical

**Transaction Information** (18 columns):
- transaction_no, transaction_date, transaction_issue_date, transaction_issuance_date
- proposal_received_date, new_login_date, proposal_modification_date
- payment_ref, mode_of_payment, payment_frequency, type_of_cheque
- receipt_no, receipt_status, cheque_no
- bank_name, bank_unique_code, account_no, loan_no, loan_type

**Branch Information** (8 columns):
- branch_code, branch_name, partner_branch_code, partner_branch_name
- zone, partner_zone_name, sub_sourcing_location, arm

**Benefit Groups** (20 columns):
- benefitgroup_1 through benefitgroup_10
- add_on_prmm_amnt_1 through add_on_prmm_amnt_10

**Tax Information** (4 columns):
- igst_amount, cgst_amount, sgst_amount, ugst_amount

**Service Provider** (2 columns):
- sp_code, sp_name

**Status and Processing** (10 columns):
- process_status_description, underwriting_decision_desc
- eximius_status, source_type, business_source_type
- cancel_decline_reason, cancel_decline_date
- stp_nstp, online_offline_type, src_typ_flg

**Previous Insurance** (4 columns):
- retail_previous_insurer_name, group_previous_insurer_name
- previous_policy_number, previous_policy_expiry_date

**Miscellaneous** (20 columns):
- login, post_year, post_month, month, run_year, run_month, run_day
- eldest_member_age, initial_nol_main_member_count
- care_shield_amount, future_gwp, per_mile_rate
- ckyc_number, pcrdate, load_date
- group_partner_cif_id, group_partner_branch_code, group_partner_rm_cd

### Data Type Mapping

Based on the CSV data analysis, each column will be documented with its data type in the format `column_name (DATA_TYPE)`:

- **STRING**: All text fields (policy_number, customer_name, agent_id, policy_type, agent_name, etc.)
- **DECIMAL**: All monetary amounts (gwp, sum_insured, premium amounts, tax amounts, total_gwp, etc.)
- **INTEGER**: Count fields (nol, initial_nol, run_day, eldest_member_age, post_year, post_month, etc.)
- **TIMESTAMP**: All date fields (risk_start_date, policy_end_date, customer_dob, transaction_date, agent_joining_date, etc.)

**Example Format in Prompt**:
```
TABLE: INSURANCE_DATA
Columns:
- policy_number (STRING)
- gwp (DECIMAL)
- initial_nol (INTEGER)
- risk_start_date (TIMESTAMP)
...
```

This format matches the existing banking schema documentation style in customer_schema_prompt, ensuring consistency across all database schema documentation.

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*


### Property 1: All CSV columns are documented
*For any* column name in the INSURANCE_DATA CSV header, that column name should appear in the insurance_schema_prompt documentation
**Validates: Requirements 1.4**

### Property 2: Example queries reference correct table
*For any* SQL query example in the insurance_schema_prompt, the FROM clause should reference INSURANCE_DATA and not INSURANCE_POLICIES or INSURANCE_CLAIMS
**Validates: Requirements 1.7**

## Error Handling

This is a documentation update with no runtime error handling requirements. The correctness is verified through:
1. Static text validation (presence/absence of specific strings)
2. Completeness checks (all columns documented)
3. Consistency checks (examples match documentation)

Potential issues:
- **Missing columns**: If columns are omitted from documentation, queries may fail or be suboptimal
- **Typos in table names**: Would cause query failures
- **Incorrect data types**: Could lead to type conversion errors in queries

Mitigation: Automated validation through property-based tests that compare documentation against source CSV.

## Testing Strategy

### Unit Tests

Unit tests will verify specific examples and edge cases:

1. **Test: Old table names removed**
   - Verify "INSURANCE_POLICIES" not in insurance_schema_prompt
   - Verify "INSURANCE_CLAIMS" not in insurance_schema_prompt
   - Verify "INSURANCE_POLICIES" not in base_prompt
   - Verify "INSURANCE_CLAIMS" not in base_prompt

2. **Test: New table name present**
   - Verify "INSURANCE_DATA" appears in insurance_schema_prompt
   - Verify "INSURANCE_DATA" appears in base_prompt table listing

3. **Test: Database routing preserved**
   - Verify 'database="insurance_db"' instruction present
   - Verify "no access restrictions" statement present

4. **Test: Banking schema unchanged**
   - Compare customer_schema_prompt before and after
   - Verify they are identical

### Property-Based Tests

Property-based tests will verify universal properties across all inputs:

**Library**: pytest with Hypothesis (Python property-based testing library)
**Configuration**: Minimum 100 iterations per property test

1. **Property Test: Column completeness**
   - **Feature: insurance-schema-update, Property 1: All CSV columns are documented**
   - Generate: List of all column names from CSV header
   - Test: For each column name, verify it appears in insurance_schema_prompt
   - Validates: Requirements 1.4

2. **Property Test: Example query correctness**
   - **Feature: insurance-schema-update, Property 2: Example queries reference correct table**
   - Generate: Extract all SQL examples from insurance_schema_prompt using regex
   - Test: For each SQL example, parse FROM clause and verify it references INSURANCE_DATA
   - Validates: Requirements 1.7

### Test Execution Approach

1. **Pre-update snapshot**: Capture current prompt.py content
2. **Apply changes**: Update insurance_schema_prompt and base_prompt
3. **Run unit tests**: Verify specific requirements
4. **Run property tests**: Verify universal properties
5. **Manual review**: Visual inspection of formatted prompt output

## Implementation Notes

### String Replacement Strategy

The update will use a complete replacement strategy rather than incremental edits:

1. **insurance_schema_prompt**: Replace entire string with new documentation
2. **base_prompt**: Use targeted string replacement for table references in specific sections

### Column Organization

Columns will be documented with their data types in the format `column_name (DATA_TYPE)`, matching the existing banking schema format. While the columns are logically grouped in this design document for clarity, the actual prompt will list all 142 columns sequentially with their data types to match the format used in customer_schema_prompt:

```
TABLE: INSURANCE_DATA
Columns:
- policy_number (STRING)
- proposal_number (STRING)
- agent_id (STRING)
- business_type (STRING)
...
- run_year (INTEGER)
- run_month (INTEGER)
```

This ensures consistency with the existing sentra_db schema documentation format.

### Backward Compatibility

This change is **not backward compatible** with queries expecting the old table structure. However, since this is a database schema change (not just documentation), the old tables no longer exist, so backward compatibility is not required.

### Documentation Format

The insurance schema will follow the same format as the banking schema for consistency:
- Section headers with visual separators
- Table name clearly identified
- Columns listed with data types in parentheses
- Mandatory rules section
- Example queries section

## Dependencies

- **Input**: `.kiro/sample_data/insurance_synthetic_data.csv` - Source of truth for column names
- **Modified File**: `Backend/agent/prompt.py` - Target file for updates
- **No External Dependencies**: This is a pure documentation update with no code logic changes

## Deployment Considerations

1. **Testing**: Must test with actual agent queries after deployment
2. **Rollback**: Keep backup of original prompt.py
3. **Validation**: Run sample insurance queries to verify agent generates correct SQL
4. **Documentation**: Update any external documentation referencing the old schema

## Success Criteria

The update is successful when:
1. All unit tests pass
2. All property-based tests pass (100 iterations each)
3. Sample insurance queries generate valid SQL against INSURANCE_DATA table
4. No references to INSURANCE_POLICIES or INSURANCE_CLAIMS remain
5. Banking schema documentation remains unchanged
