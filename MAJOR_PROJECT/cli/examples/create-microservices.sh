#!/bin/bash

# Example: Create a complete microservices architecture with Velora CLI

set -e

echo "🚀 Creating microservices architecture with Velora CLI"
echo "======================================================"

# Configuration
PROJECT_NAME="ecommerce"
GITHUB_TOKEN=${GITHUB_TOKEN:-""}
DOCKER_REGISTRY=${DOCKER_REGISTRY:-"velora"}

if [ -z "$GITHUB_TOKEN" ]; then
  echo "⚠️  GITHUB_TOKEN not set. GitHub repositories will not be created."
  echo "   Set it with: export GITHUB_TOKEN=ghp_xxxxxxxxxxxx"
fi

echo ""
echo "📋 Creating services for: $PROJECT_NAME"
echo ""

# API Services
echo "🔌 Creating API services..."

velora create ${PROJECT_NAME}-user-api \
  --type api \
  --description "User management and authentication API"

velora create ${PROJECT_NAME}-product-api \
  --type api \
  --description "Product catalog and inventory API"

velora create ${PROJECT_NAME}-order-api \
  --type api \
  --description "Order processing and payment API"

velora create ${PROJECT_NAME}-notification-api \
  --type api \
  --description "Email and push notification API"

# Frontend Services
echo ""
echo "🌐 Creating frontend services..."

velora create ${PROJECT_NAME}-web-app \
  --type frontend \
  --description "Main e-commerce web application"

velora create ${PROJECT_NAME}-admin-panel \
  --type frontend \
  --description "Admin dashboard for managing the platform"

# Worker Services  
echo ""
echo "⚙️ Creating worker services..."

velora create ${PROJECT_NAME}-email-worker \
  --type worker \
  --description "Background email processing worker"

velora create ${PROJECT_NAME}-analytics-worker \
  --type worker \
  --description "Data analytics and reporting worker"

velora create ${PROJECT_NAME}-image-processor \
  --type worker \
  --description "Product image processing and optimization"

# Database Services
echo ""
echo "🗄️ Creating database services..."

velora create ${PROJECT_NAME}-user-db \
  --type database \
  --description "User data and authentication database"

velora create ${PROJECT_NAME}-product-db \
  --type database \
  --description "Product catalog database"

velora create ${PROJECT_NAME}-analytics-db \
  --type database \
  --description "Analytics and reporting database"

# Wait for services to be created
echo ""
echo "⏳ Waiting for services to initialize..."
sleep 10

# Check status of all services
echo ""
echo "📊 Service Status:"
velora list --format table

# Monitor deployments
echo ""
echo "👀 Monitoring deployments (this may take a few minutes)..."

services=(
  "${PROJECT_NAME}-user-api"
  "${PROJECT_NAME}-product-api" 
  "${PROJECT_NAME}-order-api"
  "${PROJECT_NAME}-notification-api"
  "${PROJECT_NAME}-web-app"
  "${PROJECT_NAME}-admin-panel"
)

for service in "${services[@]}"; do
  echo "🔍 Checking $service..."
  velora status $service
  echo ""
done

echo ""
echo "🎉 Microservices architecture created successfully!"
echo ""
echo "📋 Summary:"
echo "   • 4 API services"
echo "   • 2 Frontend applications"  
echo "   • 3 Background workers"
echo "   • 3 Database services"
echo "   • Total: 12 services"
echo ""
echo "🔧 Next steps:"
echo "1. Monitor deployments: velora list"
echo "2. View service details: velora status <service-name>"
echo "3. Check logs: velora logs <service-name> --follow"
echo "4. Access web dashboard: https://your-velora-instance.com"
echo ""
echo "🚀 Happy coding with Velora!"