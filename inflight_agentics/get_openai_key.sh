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
║     OpenAI API Key Setup Assistant    ║
║     for Inflight Agentics Trading     ║
╚═══════════════════════════════════════╝
"

print_info "This script will help you set up your OpenAI API key."
echo

print_info "Steps to get your OpenAI API key:"
echo "1. Go to https://platform.openai.com/account/api-keys"
echo "2. Sign in or create an account"
echo "3. Click 'Create new secret key'"
echo "4. Copy the generated API key"
echo

# Prompt for API key
read -p "Enter your OpenAI API key: " api_key

# Validate API key format (basic check)
if [[ ! $api_key =~ ^sk-[A-Za-z0-9]{48}$ ]]; then
    print_error "Invalid API key format. It should start with 'sk-' followed by 48 characters."
    exit 1
fi

# Update .env file
if [ -f .env ]; then
    # Backup existing .env
    cp .env .env.backup
    print_status "Created backup of existing .env file as .env.backup"
    
    # Replace API key in .env
    sed -i "s/OPENAI_API_KEY=.*/OPENAI_API_KEY=$api_key/" .env
    print_status "Updated OpenAI API key in .env file"
else
    if [ -f .env.example ]; then
        cp .env.example .env
        sed -i "s/OPENAI_API_KEY=.*/OPENAI_API_KEY=$api_key/" .env
        print_status "Created .env file with your OpenAI API key"
    else
        print_error ".env.example file not found"
        exit 1
    fi
fi

print_status "OpenAI API key setup complete!"
echo
print_info "You can now run the deployment script:"
echo "./deploy.sh"
echo

print_warning "Important: Keep your API key secure and never share it"
print_warning "If you need to update the key later, run this script again"
