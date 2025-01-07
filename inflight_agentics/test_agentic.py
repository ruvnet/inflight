"""Script to test the AgenticController's decision-making capabilities."""
import json
import logging
from datetime import datetime, timezone
from inflight_agentics import AgenticController

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_agentic_decisions():
    """Test the AgenticController with various flight scenarios."""
    controller = AgenticController()
    
    # Test scenarios
    test_events = [
        {
            "flight_id": "AC1234",
            "status": "DELAYED",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "delay_minutes": 120,
            "reason": "Weather conditions"
        },
        {
            "flight_id": "UA5678",
            "status": "CANCELLED",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "reason": "Technical issues"
        },
        {
            "flight_id": "BA9012",
            "status": "ON_TIME",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "reason": "Incoming weather alerts"
        }
    ]
    
    try:
        for i, event in enumerate(test_events, 1):
            logger.info(f"\nTest {i}: Processing event...")
            logger.info(f"Event details: {json.dumps(event, indent=2)}\n")
            
            # Process the event
            action = await controller.process_event(event)
            
            # Log the results
            logger.info("Decision details:")
            logger.info("-" * 50)
            logger.info(f"Action Type: {action['action_type']}")
            logger.info(f"Confidence: {action['confidence']}")
            logger.info("\nSteps to take:")
            for j, step in enumerate(action['steps'], 1):
                logger.info(f"{j}. {step}")
            logger.info("-" * 50)
            logger.info("Test completed successfully\n")
            
    except Exception as e:
        logger.error(f"Error during test: {e}")
        raise

if __name__ == "__main__":
    import asyncio
    logger.info("Starting AgenticController test...")
    asyncio.run(test_agentic_decisions())
    logger.info("All tests completed.")
