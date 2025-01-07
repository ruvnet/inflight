"""OpenAI Realtime API integration for streaming text responses."""
import logging
import time
from typing import Optional

from openai import OpenAI
from inflight_agentics.config.settings import OPENAI_API_KEY, MAX_RETRIES, RETRY_DELAY

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RealtimeLLMClient:
    """Client for interacting with OpenAI's API."""
    
    def __init__(self):
        """Initialize the OpenAI client with API key."""
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        logger.info("RealtimeLLMClient initialized with OpenAI API key.")

    def stream_text(self, prompt: str, retries: Optional[int] = None) -> str:
        """
        Stream text from OpenAI's API based on the given prompt.

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
                logger.debug(f"Creating chat completion for prompt: {prompt}")
                response_text = ""
                
                # Create a streaming chat completion
                stream = self.client.chat.completions.create(
                    model="gpt-4",  # or "gpt-3.5-turbo" for faster, cheaper responses
                    messages=[{"role": "user", "content": prompt}],
                    stream=True,
                    temperature=0.7,
                    max_tokens=1000
                )
                
                # Process the streaming response
                print("\nStreaming response:")  # Visual indicator of streaming
                for chunk in stream:
                    if chunk.choices[0].delta.content is not None:
                        chunk_text = chunk.choices[0].delta.content
                        response_text += chunk_text
                        # Print chunk in real-time
                        print(chunk_text, end="", flush=True)
                print("\n")  # End streaming visual indicator
                
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
