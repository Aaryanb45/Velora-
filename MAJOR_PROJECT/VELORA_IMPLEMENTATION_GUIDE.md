# Velora - Complete Implementation Guide

## 🚀 Project Overview

Velora is a comprehensive Cloud-Native Internal Developer Platform (IDP) that automates and standardizes service delivery. This guide provides complete implementation instructions for all components.

## 📁 Repository Structure

```
velora/
├── cli/                     # CLI Tool (Go/Node.js)
├── web/                     # Web Application (Current React + FastAPI + MongoDB)
├── infrastructure/          # Kubernetes manifests, Terraform, etc.
├── templates/              # Service templates
├── docs/                   # Documentation
└── scripts/               # Setup and deployment scripts
```

## 🔧 Component 1: CLI Tool Implementation

### Prerequisites
- Go 1.19+ or Node.js 16+
- Access to web application API
- GitHub token
- Docker Hub credentials

### CLI Architecture

```
velora-cli/
├── cmd/
│   ├── root.go
│   ├── create.go
│   ├── deploy.go
│   ├── status.go
│   └── config.go
├── pkg/
│   ├── api/
│   ├── github/
│   ├── docker/
│   └── templates/
├── templates/
│   ├── api/
│   ├── frontend/
│   ├── worker/
│   └── database/
└── main.go
```

### Go Implementation

#### main.go
```go
package main

import (
    "github.com/spf13/cobra"
    "velora-cli/cmd"
)

func main() {
    cmd.Execute()
}
```

#### cmd/root.go
```go
package cmd

import (
    "fmt"
    "os"
    "github.com/spf13/cobra"
    "github.com/spf13/viper"
)

var cfgFile string

var rootCmd = &cobra.Command{
    Use:   "velora",
    Short: "Velora - Cloud-Native Internal Developer Platform CLI",
    Long: `Velora CLI helps developers create, deploy, and manage services
with automated CI/CD pipelines and Kubernetes deployment.`,
}

func Execute() {
    if err := rootCmd.Execute(); err != nil {
        fmt.Println(err)
        os.Exit(1)
    }
}

func init() {
    cobra.OnInitialize(initConfig)
    rootCmd.PersistentFlags().StringVar(&cfgFile, "config", "", "config file (default is $HOME/.velora.yaml)")
}

func initConfig() {
    if cfgFile != "" {
        viper.SetConfigFile(cfgFile)
    } else {
        home, err := os.UserHomeDir()
        cobra.CheckErr(err)
        viper.AddConfigPath(home)
        viper.SetConfigType("yaml")
        viper.SetConfigName(".velora")
    }

    viper.AutomaticEnv()

    if err := viper.ReadInConfig(); err == nil {
        fmt.Println("Using config file:", viper.ConfigFileUsed())
    }
}
```

#### cmd/create.go
```go
package cmd

import (
    "fmt"
    "github.com/spf13/cobra"
    "velora-cli/pkg/api"
    "velora-cli/pkg/github"
    "velora-cli/pkg/templates"
)

var (
    serviceName   string
    serviceType   string
    description   string
    githubToken   string
    dockerToken   string
)

var createCmd = &cobra.Command{
    Use:   "create [service-name]",
    Short: "Create a new service with CI/CD pipeline",
    Args:  cobra.ExactArgs(1),
    Run: func(cmd *cobra.Command, args []string) {
        serviceName = args[0]
        
        fmt.Printf("🚀 Creating service '%s' of type '%s'\n", serviceName, serviceType)
        
        // 1. Create GitHub repository
        repo, err := github.CreateRepository(serviceName, description, githubToken)
        if err != nil {
            fmt.Printf("❌ Failed to create GitHub repository: %v\n", err)
            return
        }
        fmt.Printf("✅ GitHub repository created: %s\n", repo.CloneURL)
        
        // 2. Generate and push template files
        err = templates.GenerateTemplate(serviceType, serviceName, repo.CloneURL)
        if err != nil {
            fmt.Printf("❌ Failed to generate template: %v\n", err)
            return
        }
        fmt.Printf("✅ Template files generated and pushed\n")
        
        // 3. Register service with Velora platform
        service, err := api.CreateService(serviceName, description, serviceType)
        if err != nil {
            fmt.Printf("❌ Failed to register service: %v\n", err)
            return
        }
        fmt.Printf("✅ Service registered with ID: %s\n", service.ID)
        
        // 4. Monitor pipeline
        fmt.Println("📊 Monitoring deployment pipeline...")
        api.WatchPipeline(service.ID)
        
        // 5. Get service URL
        serviceURL, err := api.GetServiceURL(service.ID)
        if err == nil {
            fmt.Printf("🌐 Service URL: %s\n", serviceURL)
        }
        
        fmt.Println("🎉 Service creation completed!")
    },
}

func init() {
    rootCmd.AddCommand(createCmd)
    createCmd.Flags().StringVarP(&serviceType, "type", "t", "api", "Service type (api, frontend, worker, database)")
    createCmd.Flags().StringVarP(&description, "description", "d", "", "Service description")
    createCmd.Flags().StringVar(&githubToken, "github-token", "", "GitHub personal access token")
    createCmd.Flags().StringVar(&dockerToken, "docker-token", "", "Docker Hub access token")
    createCmd.MarkFlagRequired("description")
    createCmd.MarkFlagRequired("github-token")
}
```

#### pkg/api/client.go
```go
package api

import (
    "bytes"
    "encoding/json"
    "fmt"
    "net/http"
    "time"
)

const (
    DefaultAPIURL = "https://velora-cloud.preview.emergentagent.com/api"
)

type Client struct {
    BaseURL    string
    HTTPClient *http.Client
}

type Service struct {
    ID          string `json:"id"`
    Name        string `json:"name"`
    Description string `json:"description"`
    ServiceType string `json:"service_type"`
    Status      string `json:"status"`
    ServiceURL  string `json:"service_url"`
}

type Pipeline struct {
    ID       string `json:"id"`
    Status   string `json:"status"`
    Stage    string `json:"stage"`
    Progress int    `json:"progress"`
    Logs     []string `json:"logs"`
}

func NewClient() *Client {
    return &Client{
        BaseURL: DefaultAPIURL,
        HTTPClient: &http.Client{
            Timeout: 30 * time.Second,
        },
    }
}

func CreateService(name, description, serviceType string) (*Service, error) {
    client := NewClient()
    
    payload := map[string]interface{}{
        "name":         name,
        "description":  description,
        "service_type": serviceType,
        "developer_id": "cli-user", // Could be configured
    }
    
    jsonData, err := json.Marshal(payload)
    if err != nil {
        return nil, err
    }
    
    resp, err := client.HTTPClient.Post(
        client.BaseURL+"/services",
        "application/json",
        bytes.NewBuffer(jsonData),
    )
    if err != nil {
        return nil, err
    }
    defer resp.Body.Close()
    
    var service Service
    err = json.NewDecoder(resp.Body).Decode(&service)
    if err != nil {
        return nil, err
    }
    
    return &service, nil
}

func WatchPipeline(serviceID string) {
    client := NewClient()
    
    for {
        resp, err := client.HTTPClient.Get(
            fmt.Sprintf("%s/services/%s/pipeline", client.BaseURL, serviceID),
        )
        if err != nil {
            time.Sleep(5 * time.Second)
            continue
        }
        
        var pipeline Pipeline
        err = json.NewDecoder(resp.Body).Decode(&pipeline)
        resp.Body.Close()
        
        if err != nil {
            time.Sleep(5 * time.Second)
            continue
        }
        
        fmt.Printf("📊 Pipeline: %s - %s (%d%%)\n", 
            pipeline.Status, pipeline.Stage, pipeline.Progress)
        
        if pipeline.Status == "success" || pipeline.Status == "failed" {
            break
        }
        
        time.Sleep(5 * time.Second)
    }
}

func GetServiceURL(serviceID string) (string, error) {
    client := NewClient()
    
    resp, err := client.HTTPClient.Get(
        fmt.Sprintf("%s/services/%s", client.BaseURL, serviceID),
    )
    if err != nil {
        return "", err
    }
    defer resp.Body.Close()
    
    var service Service
    err = json.NewDecoder(resp.Body).Decode(&service)
    if err != nil {
        return "", err
    }
    
    return service.ServiceURL, nil
}
```

#### pkg/github/client.go
```go
package github

import (
    "context"
    "github.com/google/go-github/v48/github"
    "golang.org/x/oauth2"
)

type Repository struct {
    Name     string
    CloneURL string
    SSHURL   string
}

func CreateRepository(name, description, token string) (*Repository, error) {
    ctx := context.Background()
    ts := oauth2.StaticTokenSource(
        &oauth2.Token{AccessToken: token},
    )
    tc := oauth2.NewClient(ctx, ts)
    client := github.NewClient(tc)
    
    repo := &github.Repository{
        Name:        github.String(name),
        Description: github.String(description),
        Private:     github.Bool(false),
        AutoInit:    github.Bool(true),
    }
    
    createdRepo, _, err := client.Repositories.Create(ctx, "", repo)
    if err != nil {
        return nil, err
    }
    
    return &Repository{
        Name:     *createdRepo.Name,
        CloneURL: *createdRepo.CloneURL,
        SSHURL:   *createdRepo.SSHURL,
    }, nil
}
```

### CLI Installation Methods

#### 1. Homebrew (macOS/Linux)
```bash
# Add tap
brew tap velora/cli

# Install
brew install velora-cli
```

#### 2. Curl Installer
```bash
curl -fsSL https://get.velora.dev | sh
```

#### 3. Go Install
```bash
go install github.com/velora/cli@latest
```

### CLI Usage Examples

```bash
# Configure CLI
velora config set github-token ghp_xxxx
velora config set docker-token dckr_xxxx
velora config set api-url https://velora-cloud.preview.emergentagent.com/api

# Create a new API service
velora create my-api-service --type api --description "My awesome API service"

# Create a frontend service
velora create my-frontend --type frontend --description "React frontend application"

# Check service status
velora status my-api-service

# Get service URL
velora get-url my-api-service

# List all services
velora list

# Delete a service
velora delete my-api-service
```

## 🌐 Component 2: Web Application Integration

### API Integration Points

The CLI integrates with the web application through these API endpoints:

1. **Service Management:**
   - `POST /api/services` - Create service
   - `GET /api/services/{id}` - Get service details
   - `DELETE /api/services/{id}` - Delete service

2. **Pipeline Monitoring:**
   - `GET /api/services/{id}/pipeline` - Get pipeline status
   - `POST /api/services/{id}/rollback` - Rollback service

3. **Metrics & Logs:**
   - `GET /api/services/{id}/metrics` - Get service metrics
   - `GET /api/services/{id}/logs` - Get service logs

### Authentication

```go
// Add JWT authentication to CLI
type AuthClient struct {
    Token    string
    APIKey   string
    BaseURL  string
}

func (c *AuthClient) Authenticate() error {
    // Implement OAuth2 or API key authentication
    return nil
}
```

## ☁️ Component 3: Infrastructure Setup

### AWS EKS Cluster Setup

#### 1. Prerequisites
```bash
# Install required tools
aws configure
kubectl version
eksctl version
helm version
```

#### 2. Create EKS Cluster
```bash
# Create cluster using eksctl
eksctl create cluster \
  --name velora-cluster \
  --version 1.27 \
  --region us-west-2 \
  --nodegroup-name standard-workers \
  --node-type t3.medium \
  --nodes 3 \
  --nodes-min 1 \
  --nodes-max 4 \
  --managed
```

#### 3. Terraform Configuration
```hcl
# infrastructure/terraform/main.tf
provider "aws" {
  region = var.aws_region
}

module "eks" {
  source = "terraform-aws-modules/eks/aws"
  
  cluster_name    = "velora-cluster"
  cluster_version = "1.27"
  
  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets
  
  node_groups = {
    standard = {
      desired_capacity = 3
      max_capacity     = 4
      min_capacity     = 1
      
      instance_types = ["t3.medium"]
      
      k8s_labels = {
        Environment = "production"
        Application = "velora"
      }
    }
  }
}

module "vpc" {
  source = "terraform-aws-modules/vpc/aws"
  
  name = "velora-vpc"
  cidr = "10.0.0.0/16"
  
  azs             = ["us-west-2a", "us-west-2b", "us-west-2c"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]
  
  enable_nat_gateway = true
  enable_vpn_gateway = true
  
  tags = {
    Terraform = "true"
    Environment = "production"
  }
}
```

### Jenkins Setup on EC2

#### 1. Launch EC2 Instance
```bash
# Launch Ubuntu 20.04 instance
aws ec2 run-instances \
  --image-id ami-0c55b159cbfafe1d0 \
  --count 1 \
  --instance-type t3.large \
  --key-name velora-key \
  --security-group-ids sg-xxxxxxxxx \
  --subnet-id subnet-xxxxxxxxx \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=velora-jenkins}]'
```

#### 2. Install Jenkins
```bash
#!/bin/bash
# jenkins-setup.sh

# Update system
sudo apt update

# Install Java
sudo apt install -y openjdk-11-jdk

# Add Jenkins repository
wget -q -O - https://pkg.jenkins.io/debian/jenkins.io.key | sudo apt-key add -
sudo sh -c 'echo deb https://pkg.jenkins.io/debian binary/ > /etc/apt/sources.list.d/jenkins.list'

# Install Jenkins
sudo apt update
sudo apt install -y jenkins

# Install Docker
sudo apt install -y docker.io
sudo usermod -aG docker jenkins

# Install kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# Install Helm
curl https://baltocdn.com/helm/signing.asc | sudo apt-key add -
echo "deb https://baltocdn.com/helm/stable/debian/ all main" | sudo tee /etc/apt/sources.list.d/helm-stable-debian.list
sudo apt update
sudo apt install -y helm

# Start Jenkins
sudo systemctl start jenkins
sudo systemctl enable jenkins

echo "Jenkins is installed and running on port 8080"
echo "Initial admin password:"
sudo cat /var/lib/jenkins/secrets/initialAdminPassword
```

#### 3. Jenkins Pipeline Configuration

```groovy
// Jenkinsfile template
pipeline {
    agent any
    
    environment {
        DOCKER_REGISTRY = 'velora'
        KUBECONFIG = credentials('kubeconfig')
        DOCKER_CREDENTIALS = credentials('docker-hub')
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        stage('Code Analysis') {
            steps {
                script {
                    // Run Semgrep security analysis
                    sh 'semgrep --config=auto --json --output=semgrep-results.json .'
                }
            }
        }
        
        stage('Build Docker Image') {
            steps {
                script {
                    def image = docker.build("${DOCKER_REGISTRY}/${env.JOB_NAME}:${env.BUILD_NUMBER}")
                    
                    docker.withRegistry('https://registry.hub.docker.com', 'docker-hub') {
                        image.push()
                        image.push('latest')
                    }
                }
            }
        }
        
        stage('Deploy to Kubernetes') {
            steps {
                script {
                    // Update Helm chart with new image
                    sh """
                        helm upgrade --install ${env.JOB_NAME} ./helm-chart \
                          --set image.tag=${env.BUILD_NUMBER} \
                          --set image.repository=${DOCKER_REGISTRY}/${env.JOB_NAME} \
                          --namespace default
                    """
                }
            }
        }
        
        stage('Health Check') {
            steps {
                script {
                    // Wait for deployment to be ready
                    sh "kubectl rollout status deployment/${env.JOB_NAME}"
                    
                    // Get service URL
                    def nodePort = sh(
                        script: "kubectl get svc ${env.JOB_NAME} -o jsonpath='{.spec.ports[0].nodePort}'",
                        returnStdout: true
                    ).trim()
                    
                    def nodeIP = sh(
                        script: "kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type==\"ExternalIP\")].address}'",
                        returnStdout: true
                    ).trim()
                    
                    env.SERVICE_URL = "http://${nodeIP}:${nodePort}"
                    echo "Service URL: ${env.SERVICE_URL}"
                }
            }
        }
    }
    
    post {
        always {
            script {
                // Send notification via webhook to Velora platform
                def payload = [
                    service_id: env.VELORA_SERVICE_ID,
                    status: currentBuild.currentResult,
                    build_number: env.BUILD_NUMBER,
                    service_url: env.SERVICE_URL ?: null,
                    semgrep_results: readFile('semgrep-results.json')
                ]
                
                httpRequest(
                    httpMode: 'POST',
                    url: "${env.VELORA_API_URL}/webhooks/jenkins",
                    contentType: 'APPLICATION_JSON',
                    requestBody: groovy.json.JsonOutput.toJson(payload)
                )
            }
        }
    }
}
```

### ArgoCD GitOps Setup

#### 1. Install ArgoCD
```bash
# Create namespace
kubectl create namespace argocd

# Install ArgoCD
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Expose ArgoCD server
kubectl patch svc argocd-server -n argocd -p '{"spec": {"type": "LoadBalancer"}}'

# Get admin password
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
```

#### 2. ArgoCD Application Configuration
```yaml
# infrastructure/argocd/velora-app.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: velora-services
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/velora/service-configs
    targetRevision: HEAD
    path: .
  destination:
    server: https://kubernetes.default.svc
    namespace: default
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
    - CreateNamespace=true
```

### Service Templates

#### API Service Template
```yaml
# templates/api/helm-chart/values.yaml
replicaCount: 1

image:
  repository: velora/SERVICE_NAME
  pullPolicy: IfNotPresent
  tag: "latest"

service:
  type: ClusterIP
  port: 80
  targetPort: 8000

ingress:
  enabled: true
  className: "nginx"
  annotations: {}
  hosts:
    - host: SERVICE_NAME.velora.dev
      paths:
        - path: /
          pathType: Prefix
  tls: []

resources:
  limits:
    cpu: 500m
    memory: 512Mi
  requests:
    cpu: 250m
    memory: 256Mi

autoscaling:
  enabled: true
  minReplicas: 1
  maxReplicas: 10
  targetCPUUtilizationPercentage: 80

nodeSelector: {}
tolerations: []
affinity: {}
```

#### Dockerfile Template
```dockerfile
# templates/api/Dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 📧 Email Notifications Setup

### Gmail SMTP Configuration
```go
// pkg/notifications/email.go
package notifications

import (
    "net/smtp"
    "fmt"
)

type EmailNotifier struct {
    SMTPHost     string
    SMTPPort     string
    Username     string
    Password     string
}

func (e *EmailNotifier) SendDeploymentNotification(to, serviceName, status, serviceURL string) error {
    auth := smtp.PlainAuth("", e.Username, e.Password, e.SMTPHost)
    
    subject := fmt.Sprintf("Velora: %s Deployment %s", serviceName, status)
    body := fmt.Sprintf(`
    Service: %s
    Status: %s
    URL: %s
    
    Deployed via Velora IDP
    `, serviceName, status, serviceURL)
    
    msg := fmt.Sprintf("To: %s\r\nSubject: %s\r\n\r\n%s", to, subject, body)
    
    return smtp.SendMail(
        e.SMTPHost+":"+e.SMTPPort,
        auth,
        e.Username,
        []string{to},
        []byte(msg),
    )
}
```

## 🔗 Integration Flow

### Complete Workflow

1. **Developer runs CLI:**
   ```bash
   velora create my-service --type api --description "My service"
   ```

2. **CLI creates GitHub repo** with templates:
   - Dockerfile
   - Jenkinsfile
   - Helm chart
   - Application code

3. **Jenkins pipeline triggered:**
   - Code analysis (Semgrep)
   - Docker build
   - Security scan
   - Push to registry
   - Deploy to K8s

4. **ArgoCD syncs deployment**

5. **Service becomes available**

6. **Notifications sent** via email

7. **Web dashboard updated** with service status

## 🚀 Deployment Commands

### Complete Setup Script
```bash
#!/bin/bash
# deploy-velora.sh

echo "🚀 Deploying Velora Platform..."

# 1. Create EKS cluster
echo "Creating EKS cluster..."
eksctl create cluster -f infrastructure/eks-cluster.yaml

# 2. Deploy ArgoCD
echo "Installing ArgoCD..."
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# 3. Deploy web application
echo "Deploying web application..."
kubectl apply -f infrastructure/k8s/web-app/

# 4. Configure ingress
echo "Setting up ingress..."
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm install ingress-nginx ingress-nginx/ingress-nginx

# 5. Deploy monitoring
echo "Installing monitoring..."
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install monitoring prometheus-community/kube-prometheus-stack

echo "✅ Velora Platform deployed successfully!"
echo "🌐 Web UI: https://velora.your-domain.com"
echo "🔧 ArgoCD: https://argocd.your-domain.com"
echo "📊 Grafana: https://grafana.your-domain.com"
```

## 📋 Next Steps

1. **Clone the web application repository**
2. **Set up infrastructure using Terraform/eksctl**
3. **Deploy Jenkins on EC2 with provided scripts**
4. **Install and configure ArgoCD**
5. **Build and deploy the CLI tool**
6. **Configure service templates**
7. **Set up monitoring and alerting**
8. **Create documentation and onboarding guides**

## 🎯 Testing the Complete Platform

```bash
# Test the complete flow
velora create test-service --type api --description "Test service"

# Monitor in web dashboard
open https://velora.your-domain.com

# Check ArgoCD
open https://argocd.your-domain.com

# View service
velora get-url test-service
```

This guide provides a complete blueprint for implementing the full Velora platform. Each component can be developed and deployed independently, then integrated together for the complete experience.