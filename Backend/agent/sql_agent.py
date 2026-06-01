import re
import logging
from strands import Agent
from strands.models import BedrockModel
from tools.athena_query import athena_query, set_current_user_email
from memory.memory_setup import client, memory_id
from memory.memory_hook import MemoryHookProvider
from agent.prompt import base_prompt, get_dynamic_schema_prompt
import json

logger = logging.getLogger(__name__)

class SQLQueryExecutor:
    def __init__(self, actor_id='actor_123', session_id='session_123', user_email=None, region='ap-south-1', model_id='moonshotai.kimi-k2.5'):
        logger.info("🚀 Initializing SQLQueryExecutor...")
        logger.info(f"📍 Region: {region}, Model ID: {model_id}")
        logger.info(f"👤 User Email: {user_email}")
        
        # Set the user email globally for the athena_query tool to access
        set_current_user_email(user_email)
        logger.info(f"✅ User email set in global context for security filtering")

        try:
            self.model = BedrockModel(
                model_id=model_id,
                region_name=region
            )
            logger.info("✅ BedrockModel initialized successfully for KIMI K2.")
        except Exception as e:
            logger.error("❌ Failed to initialize BedrockModel.", exc_info=True)
            raise e

        try:
            logger.info(f"🔑 Creating agent with actor_id={actor_id} and session_id={session_id}")
            
            # Get dynamic schema prompt from memory
            dynamic_schema_prompt = get_dynamic_schema_prompt()
            
            # Insurance-only system prompt with dynamic schema
            system_prompt = f"""
                {base_prompt}
                {dynamic_schema_prompt}
            """
            
            agent_state = {
                "actor_id": actor_id, 
                "session_id": session_id,
                "user_email": user_email
            }
            logger.info(f"🔑 Agent state: {agent_state}")
            logger.info("📋 Using dynamic schema prompt from memory")
            
            self.agent = Agent(
                model=self.model,
                system_prompt=system_prompt,
                tools=[athena_query],
                hooks=[MemoryHookProvider(client, memory_id)],
                state=agent_state
            )
            
            logger.info("✅ Agent created successfully with athena_query tool, memory hooks and state.")
        except Exception as e:
            logger.error("❌ Failed to initialize Agent.", exc_info=True)
            raise e

    def _save_conversation_to_memory(self, user_query, agent_response):
        """
        Save the conversation turn (user query + complete agent response) to memory.
        Creates separate memory events for USER and ASSISTANT roles in a loop.
        
        Args:
            user_query: The user's original query
            agent_response: The complete JSON response from execute_sql function
        """
        try:
            actor_id = self.agent.state.get("actor_id")
            session_id = self.agent.state.get("session_id")
            
            logger.info(f"💾 Saving conversation to memory | actor_id={actor_id} | session_id={session_id}")
            
            if not actor_id or not session_id:
                logger.warning("Skipping memory save: missing actor_id or session_id")
                return
            
            # Prepare user message
            user_text = user_query.strip()
            
            # Prepare agent response - save the complete JSON response as string
            agent_text = json.dumps(agent_response, ensure_ascii=False, indent=2)
            
            # Create separate memory events for USER and ASSISTANT in a loop
            conversation_messages = [
                (agent_text, "assistant"),
                (user_text, "user")
            ]
            
            for message_text, role in conversation_messages:
                client.create_event(
                    memory_id=memory_id,
                    actor_id=actor_id,
                    session_id=session_id,
                    messages=[(message_text, role)]
                )
                logger.info(f"✅ {role.upper()} message saved to memory ({len(str(message_text))} chars)")
            
        except Exception as e:
            logger.error(f"❌ Memory save error: {e}", exc_info=True)



    def execute_sql(self, user_query, user_id):
        logger.info(f"📝 User Query: {user_query}")
        
        user_prompt = f"User Request: {user_query}, user_id: {user_id}"

        try:
            logger.info("🔹 Invoking agent with prompt...")
            result = self.agent(user_prompt)
            logger.info(f"LLM RESULT : {result}")
            logger.info("✅ Agent invocation successful.")
        except Exception as e:
            logger.error("❌ Agent invocation failed!", exc_info=True)
            raise e

        logger.info("🔹 Extracting JSON from response...")
        result_str = str(result).strip()
        logger.info(f"Raw result length: {len(result_str)}")
        logger.info(f"Raw result (first 300 chars): {result_str[:300]}")
        
        # Find the first { and last } to extract JSON
        # This handles cases where there's text before or after the JSON
        # Special handling for moonshot.kimik2 - check for empty or incomplete responses
        if not result_str or result_str == "" or len(result_str) < 10:
            logger.error("❌ Moonshot.kimik2 returned empty or very short response")
            sql_dict = {
                "type": "text",
                "data": "",
                "explanation": "I apologize, but I encountered an issue processing your request. Please try rephrasing your question.",
                "query_executed": ""
            }
            
            return sql_dict
        
        first_brace = result_str.find('{')
        last_brace = result_str.rfind('}')
        
        # If no JSON found, agent returned plain text (e.g., asking for clarification)
        # Wrap it in proper JSON format
        if first_brace == -1 or last_brace == -1 or last_brace <= first_brace:
            logger.warning("⚠️ No JSON braces found in result - agent returned plain text")
            logger.info(f"Plain text response: {result_str}")
            
            # Wrap plain text in proper JSON format
            sql_dict = {
                "type": "text",
                "data": "",
                "explanation": result_str,
                "query_executed": ""
            }
            logger.info("✅ Wrapped plain text response in JSON format")
            logger.info(f"📊 Final SQL Dictionary: {sql_dict}")
            
            # Save the conversation to memory even for plain text responses
            self._save_conversation_to_memory(user_query, sql_dict)
            
            return sql_dict
        
        # Extract JSON content between braces
        content = result_str[first_brace:last_brace + 1]
        logger.info(f"Extracted JSON length: {len(content)}")
        logger.info(f"Extracted JSON (first 200 chars): {content[:200]}")
        logger.info("✅ JSON extraction successful.")

        try:
            logger.info("🔹 Parsing extracted JSON...")
            logger.info(f"Content to parse: {repr(content[:500])}")
            sql_dict = json.loads(content)
            logger.info("✅ JSON parsed successfully.")
            logger.info(f"📊 Final SQL Dictionary: {sql_dict}")
            
            # Save the conversation to memory after successful JSON parsing
            self._save_conversation_to_memory(user_query, sql_dict)
            
            return sql_dict
        except json.JSONDecodeError as e:
            logger.error("❌ JSON parsing failed!", exc_info=True)
            logger.error(f"Content that failed: {content}")
            logger.error(f"Content length: {len(content)}")
            
            # Fallback: wrap the content in proper JSON format
            logger.warning("⚠️ Falling back to wrapping content as plain text")
            sql_dict = {
                "type": "text",
                "data": "",
                "explanation": result_str,
                "query_executed": ""
            }
            logger.info(f"📊 Fallback SQL Dictionary: {sql_dict}")
            
            # Save the conversation to memory even for fallback responses
            self._save_conversation_to_memory(user_query, sql_dict)
            
            return sql_dict
        except Exception as e:
            logger.error("❌ Unexpected error while parsing JSON.", exc_info=True)
            raise e
