import boto3
from strands import tool
import logging
import os

logger = logging.getLogger(__name__)
REGION = os.getenv("AWS_REGION", "ap-south-1")

@tool(
    name="knowledge_base_retrieve",
    description="""Retrieve schema for different tables. The LLM can call this tool regarding any schema query for the table.
                It returns text results.""",
    inputSchema={
        "type": "object",
        "properties": {
            "query": {"type": "string"}
        },
        "required": ["query"]
    }
)


def knowledge_base_retrieve(query: str) -> str:
    """
    This tool retrieves information from the Bedrock Knowledge Base based on the provided question.
    This contains all the schema information for the tables you have access to.
    You can ask for any table schemas and column descriptions, as well as business rules and join rules.

    Args:
        query (str): Your query about the tables schema.

    Returns:
        Text response containing answer to your question..
    """
    try:
        resolved_kb_id = "TYU1K7VNHX"
        if not resolved_kb_id:
            err = "Knowledge Base ID not provided (kb_id missing and environment variable BEDROCK_KB_ID not set)"
            logger.error(err)
            return f"ERROR: {err}"

        client = boto3.client("bedrock-agent-runtime", region_name=REGION)

        try:
            response = client.retrieve(
                knowledgeBaseId=resolved_kb_id,
                retrievalQuery={"text": query},
                retrievalConfiguration={"vectorSearchConfiguration": {"numberOfResults": 5}}
            )
            logger.info("Knowledge Base Response: %s", response)
        except Exception as e:
            logger.exception("Bedrock KB retrieve API call failed")
            return f"ERROR: Bedrock KB retrieve API call failed: {str(e)}"

        try:
            retrievals = response.get("retrievalResults", [])
            if not retrievals:
                return "NO_RESULTS"
            docs = []
            for item in retrievals:
                content = item.get("content", {})
                text = content.get("text") if isinstance(content, dict) else str(content)
                if text:
                    docs.append(text)
            if not docs:
                return "NO_TEXT_IN_RESULTS"
            return "\n\n".join(docs)

        except Exception as e:
            logger.exception("Error processing retrieval results")
            return f"ERROR: processing retrieval results: {str(e)}"

    except Exception as e:
        logger.exception("knowledge_base_retrieve tool unexpected error")
        return f"ERROR: unexpected error in knowledge_base_retrieve: {str(e)}"