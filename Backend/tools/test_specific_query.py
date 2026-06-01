#!/usr/bin/env python3
"""
Test the specific query from the user
"""

import sys
sys.path.insert(0, '..')

from query_security import QuerySecurityFilter

# The query from the user
sql = "SELECT policy_type AS policy_category, COUNT(*) AS policy_count FROM insurance_data GROUP BY policy_type ORDER BY policy_count DESC"

print("=" * 100)
print("Testing Security Filter on User's Query")
print("=" * 100)

test_users = [
    "harsh.kumar@sentra.com",
    "vishal.saxena@sentra.com",
    "kamaljeet.singh@sentra.com",
    "super.admin@sentra.com"
]

for user_email in test_users:
    print(f"\n{'=' * 100}")
    print(f"User: {user_email}")
    print(f"{'=' * 100}")
    print(f"\nOriginal SQL:")
    print(f"{sql}")
    
    modified_sql, was_modified = QuerySecurityFilter.inject_security_filter(
        sql, 
        user_email, 
        "insurance_db"
    )
    
    print(f"\nModified: {was_modified}")
    print(f"\nResult SQL:")
    print(f"{modified_sql}")
    print()

print("=" * 100)
print("Expected Behavior:")
print("=" * 100)
print("""
The WHERE clause should be injected BEFORE the GROUP BY clause:

SELECT policy_type AS policy_category, COUNT(*) AS policy_count 
FROM insurance_data 
WHERE email IN (
    SELECT reportee_email 
    FROM user_data.user_data 
    WHERE self_email = 'user@sentra.com'
) 
GROUP BY policy_type 
ORDER BY policy_count DESC

This ensures:
1. Rows are filtered by user access FIRST
2. Then aggregation (COUNT) happens on filtered data
3. Then results are ordered
""")
