#!/bin/bash

# Example: Local development workflow with Velora CLI

set -e

echo "💻 Local Development Workflow with Velora CLI"
echo "============================================="

SERVICE_NAME="my-local-service"

# Step 1: Create service
echo "🚀 Step 1: Creating service..."
velora create $SERVICE_NAME \
  --type api \
  --description "Local development example service" \
  --skip-deploy

# Step 2: Clone repository locally
echo ""
echo "📥 Step 2: Setting up local development..."

# Get service info
SERVICE_INFO=$(velora status $SERVICE_NAME --json)
GITHUB_URL=$(echo $SERVICE_INFO | jq -r '.github_repo_url // empty')

if [ -n "$GITHUB_URL" ]; then
  echo "Cloning repository: $GITHUB_URL"
  
  # Extract repo name from URL
  REPO_NAME=$(basename $GITHUB_URL .git)
  
  if [ ! -d "$REPO_NAME" ]; then
    git clone $GITHUB_URL
  fi
  
  cd $REPO_NAME
  
  echo "✅ Repository cloned to $(pwd)"
else
  echo "⚠️  No GitHub repository found. Creating local directory..."
  mkdir -p $SERVICE_NAME
  cd $SERVICE_NAME
fi

# Step 3: Local development setup
echo ""
echo "🔧 Step 3: Setting up local development environment..."

# Check if we have Python files (API service)
if [ -f "requirements.txt" ]; then
  echo "Setting up Python environment..."
  
  # Create virtual environment
  if [ ! -d "venv" ]; then
    python3 -m venv venv
  fi
  
  # Activate virtual environment
  source venv/bin/activate
  
  # Install dependencies
  pip install -r requirements.txt
  
  echo "✅ Python environment ready"
  echo "💡 To activate: source venv/bin/activate"
  
elif [ -f "package.json" ]; then
  echo "Setting up Node.js environment..."
  
  # Install dependencies
  npm install
  
  echo "✅ Node.js environment ready"
  echo "💡 To start: npm start"
fi

# Step 4: Local testing
echo ""
echo "🧪 Step 4: Local testing setup..."

if [ -f "docker-compose.yml" ]; then
  echo "Docker Compose found - starting local services..."
  docker-compose up -d
  
  echo "✅ Local services started"
  echo "💡 View services: docker-compose ps"
  echo "💡 View logs: docker-compose logs -f"
  
elif [ -f "Dockerfile" ]; then
  echo "Dockerfile found - building local image..."
  docker build -t $SERVICE_NAME:local .
  
  echo "✅ Docker image built: $SERVICE_NAME:local"
  echo "💡 Run locally: docker run -p 8000:8000 $SERVICE_NAME:local"
fi

# Step 5: Development workflow
echo ""
echo "🔄 Step 5: Development workflow ready!"
echo ""
echo "📋 Available commands:"
echo "   • Test locally: make test (or npm test / pytest)"
echo "   • Build: make build (or docker build)"
echo "   • Deploy: velora deploy $SERVICE_NAME"
echo "   • View logs: velora logs $SERVICE_NAME --follow"
echo "   • Check status: velora status $SERVICE_NAME"
echo ""
echo "🔧 Development workflow:"
echo "1. Make your changes"
echo "2. Test locally: make test"
echo "3. Commit and push to GitHub"
echo "4. Deploy: velora deploy $SERVICE_NAME --follow"
echo "5. Monitor: velora status $SERVICE_NAME"
echo ""
echo "📚 Service structure:"
if [ -f "requirements.txt" ]; then
  echo "   main.py          - FastAPI application"
  echo "   requirements.txt - Python dependencies"
fi
if [ -f "package.json" ]; then
  echo "   package.json     - Node.js dependencies"
  echo "   src/             - Source code"
fi
echo "   Dockerfile       - Container definition"
echo "   helm-chart/      - Kubernetes deployment"
echo "   Jenkinsfile      - CI/CD pipeline"
echo "   .github/         - GitHub Actions"
echo ""
echo "🌐 Access your service:"
echo "   • Local: http://localhost:8000 (if running locally)"
echo "   • Production: velora status $SERVICE_NAME (for live URL)"
echo ""
echo "💡 Pro tips:"
echo "   • Use 'velora logs $SERVICE_NAME --follow' to debug issues"
echo "   • Check 'velora list' to see all your services"
echo "   • Use 'velora deploy $SERVICE_NAME --rollback' if deployment fails"
echo ""
echo "🎉 Happy coding! Your local development environment is ready."