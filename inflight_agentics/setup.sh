#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print status messages
print_info() {
    echo -e "${BLUE}[i]${NC} $1"
}

print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# ASCII art banner
echo "
╔═══════════════════════════════════════╗
║     Inflight Agentics Setup Script    ║
║      Complete System Deployment       ║
╚═══════════════════════════════════════╝
"

print_info "This script will guide you through the complete setup process."
echo

# Step 1: OpenAI API Key Setup
print_info "Step 1: OpenAI API Key Setup"
if [ -f .env ] && grep -q "^OPENAI_API_KEY=sk-" .env; then
    print_status "OpenAI API key already configured"
else
    print_info "Running OpenAI API key setup..."
    ./get_openai_key.sh
    if [ $? -ne 0 ]; then
        print_error "OpenAI API key setup failed"
        exit 1
    fi
    
    # Verify key was properly set
    if ! grep -q "^OPENAI_API_KEY=sk-" .env; then
        print_error "OpenAI API key not properly configured"
        print_warning "Please try running ./get_openai_key.sh manually"
        exit 1
    fi
fi
print_status "OpenAI API key verification successful"
echo

# Step 2: System Deployment
print_info "Step 2: System Deployment"
print_info "Running deployment script..."
./deploy.sh
if [ $? -ne 0 ]; then
    print_error "Deployment failed"
    exit 1
fi
echo

print_status "Setup complete! Your system is now ready."
echo
print_info "Access your services at:"
echo "- Kafka UI: http://localhost:8080"
echo "- View logs: docker-compose logs -f"
echo
print_warning "Remember to monitor the system and check logs regularly"
