# Inflight Agentics

A real-time event processing system for flight operations using Kafka and OpenAI's Realtime API.

## Prerequisites

- Python 3.9 or higher
- Docker and Docker Compose (for running Kafka)
- Poetry (Python package manager)
- OpenAI API key

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd inflight-agentics
```

2. Install dependencies using Poetry:
```bash
poetry install
```

3. Configure environment variables:
   - Copy `.env.example` to `.env`
   - Update the values in `.env`:
     ```
     KAFKA_BROKER_URL=localhost:9092
     KAFKA_TOPIC=flight-events
     OPENAI_API_KEY=your-openai-api-key
     LOG_LEVEL=INFO
     MAX_RETRIES=3
     RETRY_DELAY=1.0
     ```

## Running the Application

1. Start Kafka using Docker Compose:
```bash
docker-compose up -d
```

This will start:
- Zookeeper (port 2181)
- Kafka (port 9092)
- Kafka UI (port 8080) - Visit http://localhost:8080 to monitor Kafka

2. Start the consumer:
```bash
poetry run python run_consumer.py
```

3. In a separate terminal, start the producer:
```bash
poetry run python run_producer.py
```

The producer will generate simulated flight events, and the consumer will process them using the agentic controller and OpenAI's Realtime API.

4. Monitor the system:
- Watch the consumer and producer logs in their respective terminals
- Visit http://localhost:8080 to view Kafka topics and messages in the UI
- Press Ctrl+C in either terminal to stop the consumer or producer

5. When finished, stop Kafka:
```bash
docker-compose down
```

## Components

- **FlightEventProducer**: Publishes flight events to Kafka
- **FlightEventConsumer**: Consumes events and passes them to the controller
- **AgenticController**: Makes decisions about flight events using LLM
- **RealtimeLLMClient**: Integrates with OpenAI's Realtime API

## Development

Run tests:
```bash
poetry run pytest
```

Run tests with coverage:
```bash
poetry run pytest --cov=inflight_agentics
```

## License

See LICENSE file.
