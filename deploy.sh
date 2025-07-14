#!/bin/bash

# XY Oscilloscope Deployment Script
set -e

echo "🚀 Deploying XY Oscilloscope..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root for some operations
check_root() {
    if [ "$EUID" -ne 0 ]; then
        echo -e "${RED}Error: Some operations require root privileges${NC}"
        echo "Please run with sudo or as root"
        exit 1
    fi
}

# Function to create web directory and copy files
setup_web_files() {
    echo -e "${YELLOW}Setting up web files...${NC}"
    
    # Create directory
    sudo mkdir -p /var/www/kuweni
    
    # Copy web files
    sudo cp -r web/* /var/www/kuweni/
    
    # Copy audio files
    sudo cp -r audio /var/www/kuweni/
    
    # Set permissions
    sudo chown -R www-data:www-data /var/www/kuweni
    sudo chmod -R 755 /var/www/kuweni
    
    echo -e "${GREEN}✓ Web files copied to /var/www/kuweni${NC}"
}

# Function to setup systemd service
setup_service() {
    echo -e "${YELLOW}Setting up systemd service...${NC}"
    
    # Copy service file
    sudo cp key-detector.service /etc/systemd/system/
    
    # Reload systemd
    sudo systemctl daemon-reload
    
    # Enable service
    sudo systemctl enable key-detector.service
    
    echo -e "${GREEN}✓ Service enabled${NC}"
}

# Function to start service
start_service() {
    echo -e "${YELLOW}Starting key detector service...${NC}"
    
    # Start service
    sudo systemctl start key-detector.service
    
    # Check status
    if sudo systemctl is-active --quiet key-detector.service; then
        echo -e "${GREEN}✓ Service started successfully${NC}"
    else
        echo -e "${RED}✗ Service failed to start${NC}"
        echo "Check logs with: sudo journalctl -u key-detector.service -f"
        exit 1
    fi
}

# Function to check dependencies
check_dependencies() {
    echo -e "${YELLOW}Checking dependencies...${NC}"
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}Python3 is not installed${NC}"
        exit 1
    fi
    
    # Check pip packages
    python3 -c "import websockets, pynput" 2>/dev/null || {
        echo -e "${RED}Missing Python packages. Install with:${NC}"
        echo "pip3 install websockets pynput"
        exit 1
    }
    
    echo -e "${GREEN}✓ Dependencies OK${NC}"
}

# Main deployment
main() {
    echo "Starting deployment..."
    
    check_dependencies
    
    # Ask for confirmation
    read -p "Deploy to /var/www/kuweni? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Deployment cancelled"
        exit 1
    fi
    
    setup_web_files
    setup_service
    start_service
    
    echo -e "${GREEN}🎉 Deployment complete!${NC}"
    echo
    echo "Access your oscilloscope at: http://localhost/kuweni/"
    echo "Service logs: sudo journalctl -u key-detector.service -f"
    echo "Service control: sudo systemctl {start|stop|restart|status} key-detector.service"
}

# Run main function
main "$@"