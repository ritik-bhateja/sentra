import logging
from strands.hooks import AgentInitializedEvent, HookProvider, HookRegistry, MessageAddedEvent
from bedrock_agentcore.memory import MemoryClient

logger = logging.getLogger(__name__)


class MemoryHookProvider(HookProvider):
    """
    Memory hook provider for AgentCore memory integration.
    Handles loading conversation history and saving new messages.
    """
    
    def __init__(self, memory_client: MemoryClient, memory_id: str):
        """
        Initialize the memory hook provider.
        
        Args:
            memory_client: AgentCore memory client instance
            memory_id: Memory identifier for storage
        """
        self.memory_client = memory_client
        self.memory_id = memory_id
    
    def _extract_text_from_message(self, message: dict) -> str | None:
        """
        Extract user-visible text from a message in a model-agnostic way.
        Returns None if nothing suitable should be stored.
        
        Args:
            message: Message dictionary containing content blocks
            
        Returns:
            Extracted text string or None if no suitable text found
        """
        content_blocks = message.get("content", [])

        for block in content_blocks:
            # Plain text (most user messages, some assistant replies)
            if isinstance(block, dict) and isinstance(block.get("text"), str):
                return block["text"].strip()

            # Structured assistant output with explanation
            if isinstance(block, dict) and isinstance(block.get("explanation"), str):
                return block["explanation"].strip()

        return None

    def on_agent_initialized(self, event: AgentInitializedEvent):
        """
        Load recent conversation history when agent starts.
        
        Args:
            event: Agent initialization event containing agent instance
        """
        try:
            # Get session info from agent state
            actor_id = event.agent.state.get("actor_id")
            session_id = event.agent.state.get("session_id")
            
            logger.info(f"🔍 Loading memory for actor_id={actor_id}, session_id={session_id}")
            
            if not actor_id or not session_id:
                logger.warning("Missing actor_id or session_id in agent state")
                return
            
            # Load the last 5 conversation turns from memory
            recent_turns = self.memory_client.get_last_k_turns(
                memory_id=self.memory_id,
                actor_id=actor_id,
                session_id=session_id,
                k=5
            )
            
            logger.info(f"📚 Retrieved {len(recent_turns) if recent_turns else 0} turns from memory")
            
            if recent_turns:
                # Format conversation history for context
                context_messages = []
                
                # CRITICAL FIX: get_last_k_turns returns newest first, we need oldest first
                # Reverse to get chronological order (oldest to newest)
                for turn in reversed(recent_turns):
                    for message in turn:
                        role = message['role']
                        content = message['content']['text']
                        context_messages.append(f"{role}: {content}")
                
                context = "\n".join(context_messages)
                
                # Add context to agent's system prompt
                event.agent.system_prompt += f"\n\nRecent conversation:\n{context}"
                
                logger.info(f"✅ Loaded {len(recent_turns)} conversation turns (chronological order)")
                logger.info(f"🎯 Most recent message: {context_messages[-1][:100] if context_messages else 'None'}")
                
        except Exception as e:
            logger.error(f"Memory load error: {e}")

    # def on_message_added(self, event: MessageAddedEvent):
    #     """
    #     Store user-visible messages in memory.
        
    #     Args:
    #         event: Message added event containing agent and message data
    #     """
    #     try:
    #         messages = event.agent.messages
    #         logger.info("Line 109")
    #         logger.info(messages);
    #         if not messages:
    #             return

    #         last_message = messages[-1]
    #         logger.info('Line 115')
    #         logger.info(last_message)
    #         role = last_message.get("role")
    #         logger.info(role)

    #         actor_id = event.agent.state.get("actor_id")
    #         session_id = event.agent.state.get("session_id")

    #         logger.info(
    #             f"💾 Evaluating message for memory | role={role} | "
    #             f"actor_id={actor_id} | session_id={session_id}"
    #         )

    #         if not actor_id or not session_id:
    #             logger.warning("Skipping memory save: missing actor_id or session_id")
    #             return

    #         # Extract text using the helper method
    #         text = self._extract_text_from_message(last_message)

    #         if not text:
    #             logger.info("ℹ️ No user-visible text found; skipping memory save")
    #             return

    #         # Handle long content - truncate if necessary
    #         if len(text) > 5000:  # Reasonable limit for memory storage
    #             logger.info(f"📏 Message too long ({len(text)} chars), truncating for memory")
    #             text = text[:5000] + "... [truncated]"

    #         # Create memory event
    #         self.memory_client.create_event(
    #             memory_id=self.memory_id,
    #             actor_id=actor_id,
    #             session_id=session_id,
    #             messages=[(text, role)]
    #         )

    #         logger.info(f"✅ Message saved to memory ({len(text)} chars)")

        except Exception as e:
            logger.error(f"❌ Memory save error", exc_info=True)
    
    def register_hooks(self, registry: HookRegistry):
        """
        Register memory hooks with the hook registry.
        
        Args:
            registry: Hook registry to register callbacks with
        """
        # Register memory hooks
        registry.add_callback(AgentInitializedEvent, self.on_agent_initialized)