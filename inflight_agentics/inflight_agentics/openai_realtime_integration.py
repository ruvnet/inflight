"""OpenAI Realtime API integration for streaming text responses."""
import logging
import time
import asyncio
from typing import Optional

from openai import AsyncOpenAI
from inflight_agentics.config.settings import OPENAI_API_KEY, MAX_RETRIES, RETRY_DELAY

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RealtimeLLMClient:
    """Client for interacting with OpenAI's Realtime API."""
    
    def __init__(self):
        """Initialize the AsyncOpenAI client with API key."""
        self.client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        logger.info("RealtimeLLMClient initialized with OpenAI API key.")

    async def stream_text(self, prompt: str, retries: Optional[int] = None) -> str:
        """
        Stream text from OpenAI's Realtime API based on the given prompt.

        Args:
            prompt (str): The input prompt to send to the LLM.
            retries (Optional[int]): Number of retry attempts. Defaults to MAX_RETRIES.

        Returns:
            str: The concatenated response from the LLM.

        Raises:
            Exception: If all retry attempts fail.
        """
        retries = MAX_RETRIES if retries is None else retries
        attempt = 0
        last_error = None

        while attempt <= retries:
            try:
                logger.debug(f"Creating realtime connection for prompt: {prompt}")
                response_text = ""
                
                # Create a WebSocket connection with realtime model
                async with self.client.beta.realtime.connect(
                    model="gpt-4o-realtime-preview-2024-12-17"
                ) as connection:
                    # Configure session for text modality
                    await connection.session.update(session={'modalities': ['text']})

                    # Send the prompt
                    await connection.conversation.item.create(
                        item={
                            "type": "message",
                            "role": "user",
                            "content": [{"type": "input_text", "text": prompt}],
                        }
                    )
                    await connection.response.create()

                    # Process the streaming response
                    print("\nStreaming response:")  # Visual indicator of streaming
                    async for event in connection:
                        if event.type == 'response.text.delta':
                            response_text += event.delta
                            # Print chunk in real-time
                            print(event.delta, end="", flush=True)
                        elif event.type == 'response.text.done':
                            print()
                        elif event.type == "response.done":
                            break
                
                logger.info("Successfully completed streaming response from LLM.")
                return response_text

            except Exception as e:
                last_error = e
                attempt += 1
                if attempt <= retries:
                    logger.warning(
                        f"Error during streaming (attempt {attempt}/{retries}): {e}. "
                        f"Retrying in {RETRY_DELAY} seconds..."
                    )
                    time.sleep(RETRY_DELAY)
                else:
                    logger.error(f"Failed all {retries} retry attempts. Last error: {e}")
                    raise Exception(f"Failed to stream text after {retries} attempts") from last_error

    def __repr__(self) -> str:
        """Return string representation of the client."""
        return f"RealtimeLLMClient(api_key={'*' * 8})"

async def test_realtime_stream():
    """Test the realtime streaming functionality."""
    client = RealtimeLLMClient()
    prompt = "Hello! How are you today?"
    response = await client.stream_text(prompt)
    return response

if __name__ == "__main__":
    asyncio.run(test_realtime_stream())
