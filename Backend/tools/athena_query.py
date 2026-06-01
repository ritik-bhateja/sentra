import boto3
import time
from typing import Any, Dict, List, Union
from strands import tool
from tools.query_security import QuerySecurityFilter

# Global variable to store current user email (set by SQLQueryExecutor)
_current_user_email = None

def set_current_user_email(email: str):
    """Set the current user email for security filtering"""
    global _current_user_email
    _current_user_email = email

def get_current_user_email() -> str:
    """Get the current user email for security filtering"""
    global _current_user_email
    return _current_user_email

@tool(
    name="athena_query",
    description="""Execute SQL queries on AWS Athena insurance database.

CRITICAL: All queries use the insurance_db database which contains the INSURANCE_DATA table with comprehensive policy information including:
- Policy details (policy_number, policy_type, gwp, sum_insured)
- Customer information (customer_name, customer_id, customer_dob)
- Agent information (agent_name, agent_id, agent_category)
- Geographic data (zone, branch_name, customer_city)
- Premium and transaction data

The insurance_db database EXISTS and contains real insurance data.""",
    inputSchema={
        "type": "object",
        "properties": {
            "sql": {
                "type": "string", 
                "description": "The SQL query to execute against the INSURANCE_DATA table"
            },
            "database": {
                "type": "string", 
                "description": "Database name - always 'insurance_db' for insurance queries",
                "enum": ["insurance_db"],
                "default": "insurance_db"
            },
            "workgroup": {"type": "string"},
            "output_s3": {"type": "string"}
        },
        "required": ["sql"]
    }
)
def athena_query(sql: str, database: str = "insurance_db") -> Union[str, List[Dict[str, Any]]]:
    import logging
    logger = logging.getLogger(__name__)
    
    # Get user_email from global context
    user_email = get_current_user_email()
    
    logger.info(f"🔍 INSURANCE ATHENA QUERY TOOL CALLED")
    logger.info(f"   Database: {database} (insurance_db)")
    logger.info(f"   User Email: {user_email}")
    logger.info(f"   Original SQL: {sql}")
    
    # Apply security filter
    if user_email:
        if not QuerySecurityFilter.validate_user_email(user_email):
            error_msg = f"Invalid user email format: {user_email}"
            logger.error(f"   ❌ {error_msg}")
            return error_msg
        
        sql, was_modified = QuerySecurityFilter.inject_security_filter(sql, user_email, database)
        if was_modified:
            logger.info(f"   🔒 Security filter applied")
            logger.info(f"   Modified SQL: {sql}")
    else:
        logger.warning(f"   ⚠️ No user_email provided - query will run without security filter")
    
    # Ensure only insurance_db is used
    if database != "insurance_db":
        error_msg = f"Invalid database '{database}'. Only 'insurance_db' is supported for insurance queries."
        logger.error(f"   ❌ {error_msg}")
        return error_msg
    
    client = boto3.client("athena")
    workgroup = "primary"
    output_s3 = "s3://bedrock-agentcore-runtime-628897991744-ap-south-1-3m5mgapsu7/QueryOutput/"

    result_conf = {}
    if output_s3:
        result_conf["OutputLocation"] = output_s3

    try:
        resp = client.start_query_execution(
            QueryString=sql,
            QueryExecutionContext={
                'Database': database
            },
            WorkGroup=workgroup,
            ResultConfiguration=result_conf if result_conf else None
        )
        query_id = resp["QueryExecutionId"]
        logger.info(f"   Query ID: {query_id}")

        while True:
            status = client.get_query_execution(QueryExecutionId=query_id)
            state = status["QueryExecution"]["Status"]["State"]
            if state in ("SUCCEEDED", "FAILED", "CANCELLED"):
                break
            time.sleep(1)

        if state != "SUCCEEDED":
            error_msg = f"Insurance database query failed: {state}"
            logger.error(f"   ❌ {error_msg}")
            if state == "FAILED":
                reason = status["QueryExecution"]["Status"].get("StateChangeReason", "Unknown")
                error_msg += f" - Reason: {reason}"
                logger.error(f"   Failure reason: {reason}")
            return error_msg

        res = client.get_query_results(QueryExecutionId=query_id)
        rows = res["ResultSet"]["Rows"]
        
        if len(rows) == 0:
            logger.warning(f"   ⚠️ Insurance query returned 0 rows (no data found)")
            return []
        
        headers = [col["VarCharValue"] for col in rows[0]["Data"]]
        logger.info(f"   Columns: {headers}")

        data: List[Dict[str, Any]] = []
        for row in rows[1:]:
            values = [col.get("VarCharValue") for col in row["Data"]]
            row_dict = dict(zip(headers, values))
            data.append(row_dict)

        logger.info(f"   ✅ Insurance query succeeded - returned {len(data)} rows")
        if len(data) > 0:
            logger.info(f"   Sample row: {data[0]}")
        
        return data

    except Exception as e:
        error_msg = f"Error executing insurance database query: {str(e)}"
        logger.error(f"   ❌ {error_msg}")
        return error_msg
