"""Script to run the Inflight Agentics consumer."""
import logging
import signal
import sys
from inflight_agentics import FlightEventConsumer, AgenticController

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Run the consumer with agentic processing."""
    # Create the agentic controller
    controller = AgenticController()
    
    # Create the consumer with the controller's process_event method
    consumer = FlightEventConsumer(event_handler=controller.process_event)
    
    # Set up signal handling for graceful shutdown
    def signal_handler(signum, frame):
        logger.info("Received shutdown signal")
        consumer.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        logger.info("Starting Inflight Agentics consumer...")
        consumer.start()
        
        # Keep the main thread alive
        signal.pause()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        consumer.stop()

if __name__ == "__main__":
    main()
