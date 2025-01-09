# Inflight System - Deno Implementation

A TypeScript implementation of the Inflight System using Deno, featuring real-time event processing, agentic decision making, and WebSocket-based integrations.

## Features

- Real-time processing with OpenAI's streaming API
- Event-driven architecture using Redis Pub/Sub
- Type-safe implementation in TypeScript
- Modular design with clear separation of concerns
- Built with Deno for improved security and modern JavaScript features

## Prerequisites

- [Deno](https://deno.land/) 1.37 or later
- [Redis](https://redis.io/) 6.0 or later
- [Docker](https://www.docker.com/) and Docker Compose (optional)
- OpenAI API key

## Quick Start

1. Clone the repository and navigate to the project directory:
```bash
cd ui
```

2. Run the setup script:
```bash
./scripts/dev.sh setup
```

3. Edit the `.env` file with your configuration:
```bash
# Required
OPENAI_API_KEY=your-api-key-here

# Optional - defaults shown
REDIS_URL=localhost:6379
REDIS_CHANNELS=market-events,code-events,flight-events
MAX_RETRIES=3
RETRY_DELAY=1000
LOG_LEVEL=INFO
```

4. Start the development server:
```bash
./scripts/dev.sh dev
```

## Development

The project includes a development script (`scripts/dev.sh`) with several commands to help with common tasks:

```bash
# Show available commands
./scripts/dev.sh help

# Setup development environment
./scripts/dev.sh setup

# Run tests
./scripts/dev.sh test

# Format code
./scripts/dev.sh fmt

# Lint code
./scripts/dev.sh lint

# Start development server
./scripts/dev.sh dev

# Build and run with Docker
./scripts/dev.sh docker

# Clean build artifacts
./scripts/dev.sh clean
```

## Project Structure

```
.
├── src/
│   ├── agentic/         # Agentic decision making components
│   ├── openai/          # OpenAI API integration
│   ├── queue/           # Redis Pub/Sub implementation
│   ├── deps.ts          # Central dependencies
│   ├── main.ts          # Application entry point
│   └── types.d.ts       # TypeScript type definitions
├── scripts/             # Development and utility scripts
├── .env.example         # Example environment configuration
├── deno.json           # Deno configuration
├── docker-compose.yml  # Docker Compose configuration
├── Dockerfile          # Docker build configuration
├── import_map.json     # Import map for dependencies
└── tsconfig.json       # TypeScript configuration
```

## Testing

The project includes comprehensive tests for all major components:

- Unit tests for individual components
- Integration tests for Redis pub/sub
- End-to-end tests for the complete system

Run the test suite:
```bash
./scripts/dev.sh test
```

## Docker Deployment

The system can be run in Docker containers using Docker Compose:

1. Build and start the containers:
```bash
./scripts/dev.sh docker
```

This will:
- Build the Deno application container
- Start a Redis container
- Set up networking between containers
- Mount volumes for persistence
- Configure environment variables

## Architecture

### Core Components

1. **OpenAI Realtime Integration**
   - WebSocket-based streaming with OpenAI's API
   - Automatic retry handling
   - Efficient message processing

2. **Event Queue**
   - Redis Pub/Sub for real-time events
   - Reliable message delivery
   - Scalable event processing

3. **Agentic Controller**
   - Intelligent decision making
   - Event analysis and response
   - Action execution

### Data Flow

1. Events are published to Redis channels
2. The system subscribes to relevant channels
3. Events are processed by the agentic controller
4. The controller streams prompts to OpenAI
5. Decisions are made based on AI responses
6. Actions are executed based on decisions

## Contributing

1. Fork the repository
2. Create your feature branch
3. Run tests and ensure they pass
4. Format and lint your code
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
