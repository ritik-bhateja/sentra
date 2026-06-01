import re
import logging
from typing import Tuple

logger = logging.getLogger(__name__)


class QuerySecurityFilter:
    """
    Enforces row-level security on insurance_db queries by injecting WHERE clauses
    based on user hierarchy from user_data.user_data table.
    """
    
    USER_DATA_DB = "user_data"
    USER_DATA_TABLE = "user_data"
    INSURANCE_DB = "insurance_db"
    INSURANCE_TABLE = "insurance_data"
    
    @staticmethod
    def inject_security_filter(sql: str, user_email: str, database: str) -> Tuple[str, bool]:
        """
        Inject security filter into SQL query for insurance_db.
        
        Args:
            sql: Original SQL query
            user_email: Email of the logged-in user
            database: Target database name
            
        Returns:
            Tuple of (modified_sql, was_modified)
        """
        # Only apply filter to insurance_db queries
        if database != QuerySecurityFilter.INSURANCE_DB:
            logger.info(f"🔓 No security filter applied - database is '{database}' (not insurance_db)")
            return sql, False
        
        if not user_email:
            logger.warning("⚠️ No user_email provided - cannot apply security filter")
            return sql, False
        
        logger.info(f"🔒 Applying security filter for user: {user_email}")
        
        # Normalize SQL for parsing
        sql_normalized = sql.strip()
        sql_upper = sql_normalized.upper()
        
        # Build the security subquery
        security_subquery = f"""(
    SELECT reportee_email 
    FROM {QuerySecurityFilter.USER_DATA_DB}.{QuerySecurityFilter.USER_DATA_TABLE} 
    WHERE self_email = '{user_email}'
)"""
        
        # Check if query already has a WHERE clause
        has_where = 'WHERE' in sql_upper
        
        # Find the position to inject the filter
        # We need to handle: GROUP BY, ORDER BY, LIMIT, HAVING, etc.
        injection_point = len(sql_normalized)
        
        # Find the earliest clause that comes after WHERE (or would come after WHERE)
        clause_keywords = ['GROUP BY', 'ORDER BY', 'LIMIT', 'HAVING', 'UNION', 'INTERSECT', 'EXCEPT']
        earliest_clause_pos = len(sql_normalized)
        
        for keyword in clause_keywords:
            pos = sql_upper.find(keyword)
            if pos != -1 and pos < earliest_clause_pos:
                earliest_clause_pos = pos
        
        if has_where:
            # Find WHERE position
            where_pos = sql_upper.find('WHERE')
            
            # Find the end of the WHERE clause (before GROUP BY, ORDER BY, etc.)
            where_end = earliest_clause_pos
            
            # Extract the existing WHERE condition
            existing_condition = sql_normalized[where_pos + 5:where_end].strip()
            
            # Inject our security filter with AND
            security_condition = f"email IN {security_subquery}"
            new_where = f"WHERE ({existing_condition}) AND {security_condition}"
            
            # Reconstruct the query
            modified_sql = (
                sql_normalized[:where_pos] + 
                new_where + 
                (' ' + sql_normalized[where_end:] if where_end < len(sql_normalized) else '')
            )
        else:
            # No WHERE clause exists - add one
            security_condition = f"email IN {security_subquery}"
            new_where = f" WHERE {security_condition}"
            
            # Insert WHERE before any GROUP BY, ORDER BY, LIMIT, etc.
            modified_sql = (
                sql_normalized[:earliest_clause_pos] + 
                new_where + 
                (' ' + sql_normalized[earliest_clause_pos:] if earliest_clause_pos < len(sql_normalized) else '')
            )
        
        logger.info(f"✅ Security filter injected successfully")
        logger.info(f"   Original: {sql[:100]}...")
        logger.info(f"   Modified: {modified_sql[:150]}...")
        
        return modified_sql, True
    
    @staticmethod
    def validate_user_email(user_email: str) -> bool:
        """
        Validate user email format to prevent SQL injection.
        
        Args:
            user_email: Email to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not user_email:
            return False
        
        # Basic email validation pattern
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not re.match(email_pattern, user_email):
            logger.error(f"❌ Invalid email format: {user_email}")
            return False
        
        # Check for SQL injection attempts
        dangerous_chars = ["'", '"', ';', '--', '/*', '*/', 'DROP', 'DELETE', 'UPDATE', 'INSERT']
        user_email_upper = user_email.upper()
        
        for char in dangerous_chars:
            if char in user_email_upper:
                logger.error(f"❌ Potential SQL injection detected in email: {user_email}")
                return False
        
        return True
