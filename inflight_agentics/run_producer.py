"""Script to simulate and publish flight events."""
import json
import logging
import random
import time
from datetime import datetime, timedelta
from inflight_agentics import FlightEventProducer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Sample flight data for simulation
AIRLINES = ["AC", "UA", "AA", "DL", "BA"]
STATUSES = ["ON_TIME", "DELAYED", "CANCELLED"]
DELAY_REASONS = [
    "Weather conditions",
    "Technical issues",
    "Air traffic control",
    "Crew availability",
    "Previous flight delay"
]

def generate_flight_event():
    """Generate a simulated flight event."""
    flight_id = f"{random.choice(AIRLINES)}{random.randint(1000, 9999)}"
    status = random.choice(STATUSES)
    
    event = {
        "flight_id": flight_id,
        "status": status,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    
    if status == "DELAYED":
        event.update({
            "delay_minutes": random.randint(15, 180),
            "reason": random.choice(DELAY_REASONS)
        })
    
    return event

def main():
    """Run the event producer simulation."""
    producer = FlightEventProducer()
    
    try:
        logger.info("Starting Inflight Agentics event producer simulation...")
        while True:
            event = generate_flight_event()
            logger.info(f"Publishing event: {json.dumps(event, indent=2)}")
            
            # Publish the event using the flight_id as the key for partitioning
            producer.publish_event(event, key=event["flight_id"])
            
            # Wait between 2-5 seconds before generating the next event
            time.sleep(random.uniform(2, 5))
            
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        producer.close()

if __name__ == "__main__":
    main()
