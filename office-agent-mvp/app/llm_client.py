"""LLM client wrapper for OpenAI API."""
from openai import OpenAI
from . import config


# Initialize OpenAI client
client = OpenAI(api_key=config.OPENAI_API_KEY)


def chat(messages):
    """
    Send messages to OpenAI chat API and return response.

    Args:
        messages: List of message dicts with 'role' and 'content' keys
                 e.g., [{"role": "user", "content": "Hello"}]

    Returns:
        str: The assistant's response content

    Raises:
        Exception: If API call fails
    """
    try:
        response = client.chat.completions.create(
            model=config.LLM_MODEL,
            messages=messages,
            temperature=config.LLM_TEMPERATURE
        )
        return response.choices[0].message.content
    except Exception as e:
        raise Exception(f"LLM API error: {str(e)}")
