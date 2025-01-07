FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry

# Copy project files
COPY pyproject.toml poetry.lock ./
COPY inflight_agentics ./inflight_agentics
COPY run_consumer.py run_producer.py ./

# Configure Poetry and install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV KAFKA_BROKER_URL=kafka:9092

# Create a script to run both producer and consumer
RUN echo '#!/bin/bash\n\
echo "Waiting for Kafka to be ready..."\n\
sleep 10\n\
python run_consumer.py & \n\
python run_producer.py & \n\
wait' > /app/start.sh \
    && chmod +x /app/start.sh

# Command to run the service
CMD ["/app/start.sh"]
