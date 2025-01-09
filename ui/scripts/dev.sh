#!/bin/bash

# Exit on error
set -e

# Function to display help message
show_help() {
    echo "Inflight System Development Script"
    echo
    echo "Usage: ./dev.sh [command]"
    echo
    echo "Commands:"
    echo "  setup     - Install dependencies and setup environment"
    echo "  test      - Run tests"
    echo "  fmt       - Format code"
    echo "  lint      - Lint code"
    echo "  dev       - Run development server"
    echo "  docker    - Build and run with Docker"
    echo "  clean     - Clean build artifacts"
    echo "  help      - Show this help message"
}

# Function to setup environment
setup() {
    echo "Setting up development environment..."
    if [ ! -f .env ]; then
        cp .env.example .env
        echo "Created .env file from example"
    fi
    deno cache --import-map=import_map.json src/main.ts
}

# Function to run tests
run_tests() {
    echo "Running tests..."
    deno test --allow-net --allow-env --import-map=import_map.json
}

# Function to format code
format_code() {
    echo "Formatting code..."
    deno fmt src/
}

# Function to lint code
lint_code() {
    echo "Linting code..."
    deno lint src/
}

# Function to run development server
run_dev() {
    echo "Starting development server..."
    deno run --allow-net --allow-env --import-map=import_map.json src/main.ts
}

# Function to build and run with Docker
run_docker() {
    echo "Building and running with Docker..."
    docker-compose up --build
}

# Function to clean build artifacts
clean() {
    echo "Cleaning build artifacts..."
    rm -rf .deno_dir
    echo "Cleaned .deno_dir"
}

# Main script logic
case "$1" in
    "setup")
        setup
        ;;
    "test")
        run_tests
        ;;
    "fmt")
        format_code
        ;;
    "lint")
        lint_code
        ;;
    "dev")
        run_dev
        ;;
    "docker")
        run_docker
        ;;
    "clean")
        clean
        ;;
    "help"|"")
        show_help
        ;;
    *)
        echo "Unknown command: $1"
        echo
        show_help
        exit 1
        ;;
esac
