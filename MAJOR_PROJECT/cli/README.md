# Velora CLI

🚀 **Cloud-Native Internal Developer Platform CLI**

Create, deploy, and manage services with a single command.

## ⚡ Quick Start

```bash
# Install Velora CLI
npm install -g velora-cli

# Setup configuration
velora config setup

# Create your first service
velora create my-awesome-api --type api --description "My awesome API service"

# List services
velora list

# Check service status
velora status my-awesome-api

# View logs
velora logs my-awesome-api --follow
```

## 📦 Installation

### Option 1: NPM (Recommended)
```bash
npm install -g velora-cli
```

### Option 2: Binary Download
```bash
# macOS (Intel)
curl -L -o velora https://github.com/velora/cli/releases/latest/download/velora-macos-x64
chmod +x velora
sudo mv velora /usr/local/bin/

# macOS (Apple Silicon)
curl -L -o velora https://github.com/velora/cli/releases/latest/download/velora-macos-arm64
chmod +x velora
sudo mv velora /usr/local/bin/

# Windows
curl -L -o velora.exe https://github.com/velora/cli/releases/latest/download/velora-win-x64.exe

# Linux
curl -L -o velora https://github.com/velora/cli/releases/latest/download/velora-linux-x64
chmod +x velora
sudo mv velora /usr/local/bin/
```

### Option 3: Homebrew (macOS/Linux)
```bash
brew tap velora/tap
brew install velora-cli
```

### Option 4: Curl Installer
```bash
curl -fsSL https://get.velora.dev | sh
```

## 🔧 Configuration

### Interactive Setup
```bash
velora config setup
```

### Manual Configuration
```bash
# Set API endpoint
velora config set apiUrl https://your-velora-instance.com/api

# Set GitHub token (for repository creation)
velora config set githubToken ghp_xxxxxxxxxxxx

# Set Docker registry
velora config set dockerRegistry your-registry

# View current config
velora config list
```

## 📋 Commands

### Service Management

#### Create Service
```bash
velora create <service-name> [options]

Options:
  -t, --type <type>           Service type (api, frontend, worker, database)
  -d, --description <desc>    Service description
  --skip-github              Skip GitHub repository creation
  --skip-deploy              Skip initial deployment
```

#### List Services
```bash
velora list [options]

Options:
  -f, --format <format>       Output format (table, json)
  --status <status>          Filter by status
  --type <type>              Filter by service type
```

#### Service Status
```bash
velora status <service-name> [options]

Options:
  -f, --follow               Follow pipeline progress
  --json                     Output in JSON format
```

#### View Logs
```bash
velora logs <service-name> [options]

Options:
  -f, --follow               Follow logs in real-time
  -n, --lines <number>       Number of lines to show
```

#### Deploy/Rollback
```bash
velora deploy <service-name> [options]

Options:
  -f, --follow               Follow deployment progress
  --rollback                 Rollback to previous version
```

#### Delete Service
```bash
velora delete <service-name> [options]

Options:
  -f, --force                Force delete without confirmation
```

### Configuration
```bash
velora config setup          # Interactive setup wizard
velora config list           # List all configuration
velora config set <key> <val> # Set configuration value
velora config get <key>      # Get configuration value
velora config reset          # Reset to defaults
```

## 🏗️ Service Types

### 🔌 API Service
- **Framework**: FastAPI or Express.js
- **Features**: REST API, health checks, metrics
- **Deployment**: Auto-scaling Kubernetes deployment

```bash
velora create my-api --type api --description "REST API service"
```

### 🌐 Frontend Service
- **Framework**: React, Vue, or static sites
- **Features**: CDN integration, SSL certificates
- **Deployment**: Nginx with ingress

```bash
velora create my-frontend --type frontend --description "React frontend app"
```

### ⚙️ Worker Service
- **Framework**: Background job processing
- **Features**: Queue integration, auto-scaling
- **Deployment**: Kubernetes jobs/deployments

```bash
velora create my-worker --type worker --description "Background job processor"
```

### 🗄️ Database Service
- **Options**: PostgreSQL, MongoDB, Redis
- **Features**: Persistent storage, backups
- **Deployment**: StatefulSets with volumes

```bash
velora create my-db --type database --description "PostgreSQL database"
```

## 🔄 Workflow

1. **Create Service**
   ```bash
   velora create my-service --type api --description "My awesome service"
   ```

2. **Monitor Deployment**
   ```bash
   velora status my-service --follow
   ```

3. **Check Logs**
   ```bash
   velora logs my-service --follow
   ```

4. **Scale or Update**
   ```bash
   velora deploy my-service --follow
   ```

## 🎯 What Happens When You Create a Service?

### 1. Service Registration
- Service registered in Velora platform
- Metadata stored and tracked

### 2. GitHub Repository (Optional)
- Repository created with your GitHub token
- Template files added (Dockerfile, Helm charts, CI/CD)
- Ready for development

### 3. CI/CD Pipeline
- Jenkins pipeline automatically configured
- Security scanning (Semgrep)
- Docker image build and push
- Kubernetes deployment

### 4. Service Access
- Service URL provided
- Health checks enabled
- Monitoring and logging started

## 🔗 Integration

### GitHub Integration
```bash
# Get GitHub token from: https://github.com/settings/tokens
velora config set githubToken ghp_xxxxxxxxxxxx
```

Required permissions:
- `repo` (repository access)
- `workflow` (GitHub Actions)

### Docker Registry
```bash
# Docker Hub token from: https://hub.docker.com/settings/security
velora config set dockerToken dckr_xxxxxxxxxxxx
velora config set dockerRegistry your-username
```

### Kubernetes
```bash
# Kubeconfig for deployment
velora config set kubeconfig ~/.kube/config
```

## 🐛 Troubleshooting

### CLI Not Found
```bash
# If installed with npm but not found
npm config get prefix
# Add to PATH: export PATH=$PATH:$(npm config get prefix)/bin
```

### API Connection Issues
```bash
# Check configuration
velora config list

# Test API connection
velora --version

# Update API URL
velora config set apiUrl https://your-velora-instance.com/api
```

### GitHub Repository Creation Failed
```bash
# Check token permissions
velora config get githubToken

# Update token
velora config set githubToken ghp_xxxxxxxxxxxx
```

### Pipeline Not Starting
- Check GitHub webhook configuration
- Verify Jenkins integration
- Check repository permissions

## 🚀 Advanced Usage

### Custom Templates
Create your own service templates by forking the repository and customizing the template generation logic.

### Environment-Specific Deployment
```bash
# Deploy to staging
velora deploy my-service --env staging

# Deploy to production
velora deploy my-service --env production
```

### Batch Operations
```bash
# List all failed services
velora list --status failed --format json | jq -r '.[].name'

# Rollback multiple services
for service in $(velora list --status failed --format json | jq -r '.[].name'); do
  velora deploy $service --rollback
done
```

## 📚 Examples

### Complete Service Creation Flow
```bash
# 1. Setup CLI
velora config setup

# 2. Create API service
velora create user-service \
  --type api \
  --description "User management API"

# 3. Monitor deployment
velora status user-service --follow

# 4. Check service is running
velora list --status running

# 5. View live logs
velora logs user-service --follow

# 6. Access service
curl $(velora status user-service --json | jq -r '.service_url')
```

### Microservices Architecture
```bash
# Create multiple related services
velora create user-api --type api --description "User management API"
velora create user-frontend --type frontend --description "User management UI"
velora create user-worker --type worker --description "User background jobs"
velora create user-db --type database --description "User database"

# Monitor all services
velora list
```

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📄 License

MIT License - see LICENSE file for details.

## 🆘 Support

- 📧 Email: support@velora.dev
- 💬 Discord: https://discord.gg/velora
- 📖 Documentation: https://docs.velora.dev
- 🐛 Issues: https://github.com/velora/cli/issues

---

**Made with ❤️ for developers, by developers**