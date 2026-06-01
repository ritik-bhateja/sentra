#!/usr/bin/env python3
"""
Quick test script for QuerySecurityFilter
"""

from query_security import QuerySecurityFilter

def test_security_filter():
    print("=" * 80)
    print("Testing QuerySecurityFilter")
    print("=" * 80)
    
    test_cases = [
        {
            "name": "Simple SELECT without WHERE",
            "sql": "SELECT * FROM insurance_data",
            "user_email": "harsh.kumar@sentra.com",
            "database": "insurance_db"
        },
        {
            "name": "SELECT with existing WHERE clause",
            "sql": "SELECT * FROM insurance_data WHERE policy_type = 'Health'",
            "user_email": "vishal.saxena@sentra.com",
            "database": "insurance_db"
        },
        {
            "name": "SELECT with GROUP BY",
            "sql": "SELECT policy_type, COUNT(*) FROM insurance_data GROUP BY policy_type",
            "user_email": "kamaljeet.singh@sentra.com",
            "database": "insurance_db"
        },
        {
            "name": "SELECT with WHERE and ORDER BY",
            "sql": "SELECT * FROM insurance_data WHERE gwp > 10000 ORDER BY gwp DESC",
            "user_email": "super.admin@sentra.com",
            "database": "insurance_db"
        },
        {
            "name": "SELECT with WHERE, GROUP BY, and LIMIT",
            "sql": "SELECT agent_name, SUM(gwp) as total FROM insurance_data WHERE zone = 'North' GROUP BY agent_name LIMIT 10",
            "user_email": "harsh.kumar@sentra.com",
            "database": "insurance_db"
        },
        {
            "name": "Non-insurance database (should not modify)",
            "sql": "SELECT * FROM customer_master",
            "user_email": "harsh.kumar@sentra.com",
            "database": "sentra_db"
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{'=' * 80}")
        print(f"Test Case {i}: {test['name']}")
        print(f"{'=' * 80}")
        print(f"Database: {test['database']}")
        print(f"User: {test['user_email']}")
        print(f"\nOriginal SQL:")
        print(f"  {test['sql']}")
        
        modified_sql, was_modified = QuerySecurityFilter.inject_security_filter(
            test['sql'], 
            test['user_email'], 
            test['database']
        )
        
        print(f"\nModified: {was_modified}")
        print(f"Result SQL:")
        print(f"  {modified_sql}")
    
    print(f"\n{'=' * 80}")
    print("Email Validation Tests")
    print(f"{'=' * 80}")
    
    validation_tests = [
        ("harsh.kumar@sentra.com", True),
        ("super.admin@sentra.com", True),
        ("invalid-email", False),
        ("test@test", False),
        ("'; DROP TABLE users; --", False),
        ("test@example.com'; DELETE FROM data; --", False),
    ]
    
    for email, expected in validation_tests:
        result = QuerySecurityFilter.validate_user_email(email)
        status = "✅ PASS" if result == expected else "❌ FAIL"
        print(f"{status} | Email: {email:40} | Valid: {result} | Expected: {expected}")
    
    print(f"\n{'=' * 80}")
    print("All tests completed!")
    print(f"{'=' * 80}\n")


if __name__ == "__main__":
    test_security_filter()
