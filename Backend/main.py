from bedrock_agentcore.runtime import BedrockAgentCoreApp
from agent.sql_agent import SQLQueryExecutor
import logging
import json
import sys

logger = logging.getLogger(__name__)

app = BedrockAgentCoreApp()

@app.entrypoint
def main(payload, context = None):
    print("🔥 PRINT TEST: Entrypoint invoked")
    logging.getLogger().handlers.clear()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )

    logger = logging.getLogger(__name__)
    logger.info("🚀 Entrypoint triggered for Bedrock Agent Core App.")
    logger.info(f"📩 Incoming payload: {payload}")
    
    # Extract and validate user_id
    user_id = payload.get("user_id")
    if not user_id:
        logger.error("❌ Missing user_id in payload")
        return {
            "type": "text",
            "data": "",
            "explanation": "Error: user_id is required for memory isolation",
            "query_executed": ""
        }
    
    # Extract user_email for security filtering
    user_email = payload.get("user_email")
    
    # Normalize user_email to proper email format
    if user_email and '@' not in user_email:
        # user_email provided but not in email format (e.g., "harsh.kumar")
        user_email = f"{user_email}@sentra.com"
        logger.info(f"👤 User email normalized: {user_email}")
    elif not user_email:
        # No user_email provided, construct from user_id
        if '@' in user_id:
            user_email = user_id
        else:
            user_email = f"{user_id}@sentra.com"
        logger.info(f"👤 User email constructed from user_id: {user_email}")
    else:
        # user_email is already in proper format
        logger.info(f"👤 User email from payload: {user_email}")
    
    # Extract and validate session_id
    session_id = payload.get("session_id")
    if not session_id:
        logger.error("❌ Missing session_id in payload")
        return {
            "type": "text",
            "data": "",
            "explanation": "Error: session_id is required for memory isolation",
            "query_executed": ""
        }
    
    # Sanitize user_id for use as actor_id (AWS Bedrock Memory requirement)
    # actor_id must match pattern: [a-zA-Z0-9][a-zA-Z0-9-_/]*
    # Replace periods and other invalid characters with underscores
    actor_id = user_id.replace('.', '_').replace('@', '_at_').replace(' ', '_')
    
    logger.info(f"✅ Validated identifiers - user_id: {user_id}, actor_id: {actor_id}, session_id: {session_id}")
    
    # Initialize SQLQueryExecutor with dynamic identifiers and user_email
    generator = SQLQueryExecutor(actor_id=actor_id, session_id=session_id, user_email=user_email)
    try:
        
        result = generator.execute_sql(payload.get("user_query", ""), user_id)
        logger.info("✅ SQL execution completed successfully.")
        return result
    except Exception as e:
        logger.error("❌ Entrypoint execution failed!", exc_info=True)
        return {
                    "type": "text",
                    "data": "",
                    "explanation": f"Something went wrong while executing the query. Check the logs for more details. Error: {str(e)}",
                    "query_executed": ""
                }

if __name__ == "__main__":
    app.run()