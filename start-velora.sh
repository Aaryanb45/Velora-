#!/bin/bash

# Velora Platform Startup Script
# This script starts all Velora services locally

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting Velora Platform${NC}"
echo "============================"

# Check if MongoDB is running
echo -e "${YELLOW}📋 Checking prerequisites...${NC}"

# Check MongoDB
if ! pgrep -x "mongod" > /dev/null; then
    echo -e "${YELLOW}⚠️  MongoDB not running. Starting MongoDB...${NC}"
    
    # Try to start MongoDB (adjust command based on your system)
    if command -v brew &> /dev/null; then
        # macOS with Homebrew
        brew services start mongodb-community
    elif command -v systemctl &> /dev/null; then
        # Linux with systemd
        sudo systemctl start mongod
    else
        echo -e "${RED}❌ Cannot start MongoDB automatically. Please start it manually:${NC}"
        echo -e "${YELLOW}mongod --dbpath ./data/db${NC}"
        exit 1
    fi
    
    # Wait for MongoDB to start
    sleep 3
fi

# Check if MongoDB is accessible
if ! mongosh --eval "db.runCommand({ping:1})" &> /dev/null; then
    echo -e "${RED}❌ MongoDB is not accessible. Please check your MongoDB installation.${NC}"
    echo -e "${YELLOW}Try: mongod --dbpath ./data/db${NC}"
    exit 1
fi

echo -e "${GREEN}✅ MongoDB is running${NC}"

# Check if required dependencies are installed
echo -e "${YELLOW}📦 Checking dependencies...${NC}"

# Check Python dependencies
if [ ! -f "backend/requirements.txt" ]; then
    echo -e "${RED}❌ Backend requirements.txt not found${NC}"
    exit 1
fi

# Check Node.js dependencies
if [ ! -d "frontend/node_modules" ]; then
    echo -e "${YELLOW}⚠️  Frontend dependencies not installed. Installing...${NC}"
    cd frontend
    yarn install
    cd ..
fi

if [ ! -d "cli/node_modules" ]; then
    echo -e "${YELLOW}⚠️  CLI dependencies not installed. Installing...${NC}"
    cd cli
    npm install
    cd ..
fi

echo -e "${GREEN}✅ Dependencies checked${NC}"

# Check environment files
echo -e "${YELLOW}🔧 Checking configuration...${NC}"

if [ ! -f "backend/.env" ]; then
    echo -e "${RED}❌ Backend .env file not found${NC}"
    echo -e "${YELLOW}Please create backend/.env with required environment variables${NC}"
    exit 1
fi

if [ ! -f "frontend/.env" ]; then
    echo -e "${RED}❌ Frontend .env file not found${NC}"
    echo -e "${YELLOW}Please create frontend/.env with REACT_APP_BACKEND_URL=http://localhost:8001${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Configuration files found${NC}"

# Function to start services
start_backend() {
    echo -e "${BLUE}🐍 Starting Backend (FastAPI)...${NC}"
    cd backend
    python -m uvicorn server:app --host 0.0.0.0 --port 8001 --reload &
    BACKEND_PID=$!
    cd ..
    echo -e "${GREEN}✅ Backend started (PID: $BACKEND_PID)${NC}"
    sleep 3
}

start_frontend() {
    echo -e "${BLUE}⚛️  Starting Frontend (React)...${NC}"
    cd frontend
    yarn start &
    FRONTEND_PID=$!
    cd ..
    echo -e "${GREEN}✅ Frontend started (PID: $FRONTEND_PID)${NC}"
    sleep 3
}

# Start services
echo -e "${BLUE}🚀 Starting services...${NC}"

start_backend
start_frontend

# Wait for services to be ready
echo -e "${YELLOW}⏳ Waiting for services to be ready...${NC}"

# Check backend health
for i in {1..30}; do
    if curl -s http://localhost:8001/api/health > /dev/null; then
        echo -e "${GREEN}✅ Backend is ready!${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}❌ Backend failed to start properly${NC}"
        exit 1
    fi
    sleep 1
done

# Check frontend
for i in {1..60}; do
    if curl -s http://localhost:3000 > /dev/null; then
        echo -e "${GREEN}✅ Frontend is ready!${NC}"
        break
    fi
    if [ $i -eq 60 ]; then
        echo -e "${RED}❌ Frontend failed to start properly${NC}"
        exit 1
    fi
    sleep 1
done

# Success message
echo ""
echo -e "${GREEN}🎉 Velora Platform is running!${NC}"
echo ""
echo -e "${BLUE}📋 Service URLs:${NC}"
echo -e "  • Frontend:  ${YELLOW}http://localhost:3000${NC}"
echo -e "  • Backend:   ${YELLOW}http://localhost:8001${NC}"
echo -e "  • API Docs:  ${YELLOW}http://localhost:8001/docs${NC}"
echo ""
echo -e "${BLUE}🛠️  CLI Setup:${NC}"
echo -e "  ${YELLOW}cd cli && npm link${NC}  # Install CLI globally"
echo -e "  ${YELLOW}velora config setup${NC}  # Configure CLI"
echo ""
echo -e "${BLUE}📖 Quick Commands:${NC}"
echo -e "  ${YELLOW}velora create my-service --type api --description 'My first service'${NC}"
echo -e "  ${YELLOW}velora list${NC}"
echo -e "  ${YELLOW}velora status my-service${NC}"
echo ""
echo -e "${BLUE}🌐 Web Dashboard:${NC}"
echo -e "  Open ${YELLOW}http://localhost:3000${NC} in your browser"
echo ""
echo -e "${RED}⚠️  To stop all services, press Ctrl+C${NC}"

# Function to cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}🛑 Stopping Velora services...${NC}"
    
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
        echo -e "${GREEN}✅ Backend stopped${NC}"
    fi
    
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
        echo -e "${GREEN}✅ Frontend stopped${NC}"
    fi
    
    # Kill any remaining processes
    pkill -f "uvicorn server:app" 2>/dev/null || true
    pkill -f "react-scripts start" 2>/dev/null || true
    
    echo -e "${BLUE}👋 Velora Platform stopped. Goodbye!${NC}"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Keep the script running
while true; do
    sleep 1
done