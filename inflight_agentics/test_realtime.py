"""Script to test OpenAI Realtime API integration."""
import logging
import asyncio
from inflight_agentics import RealtimeLLMClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_realtime_api():
    """Test the OpenAI Realtime API with a sample prompt."""
    client = RealtimeLLMClient()
    
    # Test prompts simulating flight scenarios
    test_prompts = [
        """Flight AC1234 is currently DELAYED as of 2024-01-07T10:00:00Z. 
        The flight is delayed by 120 minutes. The reason given is: Weather conditions. 
        Based on this information, what action should be taken? Consider passenger impact, 
        operational constraints, and airline policies.""",
        
        """Flight UA5678 is currently CANCELLED as of 2024-01-07T11:00:00Z. 
        The reason given is: Technical issues. Based on this information, what action 
        should be taken? Consider passenger impact, operational constraints, and airline policies.""",
        
        """Flight BA9012 is currently ON_TIME as of 2024-01-07T12:00:00Z. 
        However, there are incoming weather alerts. Based on this information, what action 
        should be taken? Consider passenger impact, operational constraints, and airline policies."""
    ]
    
    try:
        for i, prompt in enumerate(test_prompts, 1):
            logger.info(f"\nTest {i}: Sending prompt to OpenAI Realtime API...")
            logger.info(f"Prompt: {prompt}\n")
            
            # Get streaming response
            response = await client.stream_text(prompt)
            
            logger.info(f"Response received:")
            logger.info("-" * 50)
            logger.info(response)
            logger.info("-" * 50)
            logger.info("Test completed successfully\n")
            
    except Exception as e:
        logger.error(f"Error during test: {e}")
        raise

if __name__ == "__main__":
    logger.info("Starting OpenAI Realtime API test...")
    asyncio.run(test_realtime_api())
    logger.info("All tests completed.")
