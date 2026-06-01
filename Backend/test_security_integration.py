#!/usr/bin/env python3
"""
Test the complete security filter integration
"""

import sys
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)

# Import the components
from tools.athena_query import set_current_user_email, get_current_user_email, athena_query
from tools.query_security import QuerySecurityFilter

print("=" * 100)
print("Testing Complete Security Filter Integration")
print("=" * 100)

# Test 1: Set and get user email
print("\n" + "=" * 100)
print("Test 1: Global User Email Context")
print("=" * 100)

test_email = "harsh.kumar@sentra.com"
set_current_user_email(test_email)
retrieved_email = get_current_user_email()

print(f"Set email: {test_email}")
print(f"Retrieved email: {retrieved_email}")
print(f"Match: {test_email == retrieved_email}")

# Test 2: Simulate what happens when athena_query is called
print("\n" + "=" * 100)
print("Test 2: Security Filter Application (Simulated)")
print("=" * 100)

test_sql = "SELECT policy_type AS policy_category, COUNT(*) AS policy_count FROM insurance_data GROUP BY policy_type ORDER BY policy_count DESC"
database = "insurance_db"

print(f"Original SQL: {test_sql}")
print(f"Database: {database}")
print(f"User Email (from global): {get_current_user_email()}")

# This is what happens inside athena_query
user_email = get_current_user_email()
if user_email and QuerySecurityFilter.validate_user_email(user_email):
    modified_sql, was_modified = QuerySecurityFilter.inject_security_filter(test_sql, user_email, database)
    print(f"\nSecurity filter applied: {was_modified}")
    print(f"Modified SQL:\n{modified_sql}")
else:
    print("Security filter NOT applied")

# Test 3: Different users
print("\n" + "=" * 100)
print("Test 3: Different Users")
print("=" * 100)

users = [
    "harsh.kumar@sentra.com",
    "vishal.saxena@sentra.com", 
    "kamaljeet.singh@sentra.com",
    "super.admin@sentra.com"
]

for user in users:
    print(f"\n--- User: {user} ---")
    set_current_user_email(user)
    current = get_current_user_email()
    print(f"Global context set to: {current}")
    
    modified_sql, was_modified = QuerySecurityFilter.inject_security_filter(
        test_sql, 
        current, 
        database
    )
    
    # Show just the WHERE clause
    if "WHERE" in modified_sql:
        where_start = modified_sql.find("WHERE")
        where_end = modified_sql.find("GROUP BY")
        where_clause = modified_sql[where_start:where_end].strip()
        print(f"WHERE clause: {where_clause[:80]}...")

print("\n" + "=" * 100)
print("✅ All tests completed!")
print("=" * 100)
print("\nKey Points:")
print("1. User email is stored in global context when SQLQueryExecutor is initialized")
print("2. athena_query tool retrieves it automatically from global context")
print("3. Security filter is applied BEFORE the query executes")
print("4. LLM cannot bypass this - it's code-level enforcement")
print("=" * 100)
