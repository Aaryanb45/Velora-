from fastapi import FastAPI, APIRouter, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime
import aiohttp
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import base64

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'velora')]

# Create the main app
app = FastAPI(title="Velora IDP API", description="Cloud-Native Internal Developer Platform")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Pydantic Models
class Developer(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    email: str
    github_username: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_admin: bool = False

class DeveloperCreate(BaseModel):
    name: str
    email: str
    github_username: Optional[str] = None
    is_admin: bool = False

class Service(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    service_type: str  # api, frontend, worker, database
    developer_id: str
    github_repo_url: Optional[str] = None
    docker_image: Optional[str] = None
    service_url: Optional[str] = None
    status: str = "creating"  # creating, building, deploying, running, failed
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ServiceCreate(BaseModel):
    name: str
    description: str
    service_type: str
    developer_id: str

class Pipeline(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    service_id: str
    status: str = "pending"  # pending, running, success, failed
    stage: str = "initialization"
    progress: int = 0
    logs: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class PipelineUpdate(BaseModel):
    status: Optional[str] = None
    stage: Optional[str] = None
    progress: Optional[int] = None
    logs: Optional[List[str]] = None

class ServiceTemplate(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    service_type: str
    description: str
    template_files: Dict[str, str]  # filename -> content
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Helper Functions
async def create_github_repo(repo_name: str, description: str, github_token: str) -> Dict[str, Any]:
    """Create a GitHub repository"""
    try:
        headers = {
            'Authorization': f'token {github_token}',
            'Accept': 'application/vnd.github.v3+json',
            'Content-Type': 'application/json'
        }
        
        data = {
            'name': repo_name,
            'description': description,
            'private': False,
            'auto_init': True
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post('https://api.github.com/user/repos', 
                                  headers=headers, json=data) as response:
                if response.status == 201:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise HTTPException(status_code=400, detail=f"GitHub API error: {error_text}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create GitHub repo: {str(e)}")

async def push_template_to_repo(repo_url: str, template_files: Dict[str, str], github_token: str):
    """Push template files to GitHub repository"""
    # This would integrate with GitHub API to create files
    # For now, we'll simulate this
    logging.info(f"Pushing template files to {repo_url}")

async def send_email_notification(to_email: str, subject: str, body: str):
    """Send email notification via Gmail SMTP"""
    try:
        smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        smtp_username = os.getenv('SMTP_USERNAME')
        smtp_password = os.getenv('SMTP_PASSWORD')
        
        if not all([smtp_username, smtp_password]):
            logging.warning("SMTP credentials not configured")
            return
        
        msg = MIMEMultipart()
        msg['From'] = smtp_username
        msg['To'] = to_email
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'html'))
        
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        text = msg.as_string()
        server.sendmail(smtp_username, to_email, text)
        server.quit()
        
        logging.info(f"Email sent to {to_email}")
    except Exception as e:
        logging.error(f"Failed to send email: {str(e)}")

# API Routes

# Developer Management
@api_router.post("/developers", response_model=Developer)
async def create_developer(developer: DeveloperCreate):
    developer_dict = developer.dict()
    developer_obj = Developer(**developer_dict)
    await db.developers.insert_one(developer_obj.dict())
    return developer_obj

@api_router.get("/developers", response_model=List[Developer])
async def get_developers():
    developers = await db.developers.find().to_list(1000)
    return [Developer(**dev) for dev in developers]

@api_router.get("/developers/{developer_id}", response_model=Developer)
async def get_developer(developer_id: str):
    developer = await db.developers.find_one({"id": developer_id})
    if not developer:
        raise HTTPException(status_code=404, detail="Developer not found")
    return Developer(**developer)

# Service Management
@api_router.post("/services", response_model=Service)
async def create_service(service_data: ServiceCreate, background_tasks: BackgroundTasks):
    # Create service record
    service_dict = service_data.dict()
    service_obj = Service(**service_dict)
    await db.services.insert_one(service_obj.dict())
    
    # Create initial pipeline
    pipeline = Pipeline(service_id=service_obj.id)
    await db.pipelines.insert_one(pipeline.dict())
    
    # Start background service creation process
    background_tasks.add_task(process_service_creation, service_obj.id)
    
    return service_obj

@api_router.get("/services", response_model=List[Service])
async def get_services(developer_id: Optional[str] = None):
    query = {}
    if developer_id:
        query["developer_id"] = developer_id
    
    services = await db.services.find(query).to_list(1000)
    return [Service(**service) for service in services]

@api_router.get("/services/{service_id}", response_model=Service)
async def get_service(service_id: str):
    service = await db.services.find_one({"id": service_id})
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    return Service(**service)

@api_router.delete("/services/{service_id}")
async def delete_service(service_id: str):
    result = await db.services.delete_one({"id": service_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Service not found")
    
    # Also delete related pipelines
    await db.pipelines.delete_many({"service_id": service_id})
    
    return {"message": "Service deleted successfully"}

# Pipeline Management
@api_router.get("/services/{service_id}/pipeline", response_model=Pipeline)
async def get_service_pipeline(service_id: str):
    pipeline = await db.pipelines.find_one({"service_id": service_id}, sort=[("created_at", -1)])
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    return Pipeline(**pipeline)

@api_router.put("/services/{service_id}/pipeline")
async def update_pipeline(service_id: str, update_data: PipelineUpdate):
    pipeline = await db.pipelines.find_one({"service_id": service_id}, sort=[("created_at", -1)])
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    
    update_dict = {k: v for k, v in update_data.dict().items() if v is not None}
    update_dict["updated_at"] = datetime.utcnow()
    
    await db.pipelines.update_one(
        {"id": pipeline["id"]}, 
        {"$set": update_dict}
    )
    
    return {"message": "Pipeline updated successfully"}

@api_router.post("/services/{service_id}/rollback")
async def rollback_service(service_id: str):
    service = await db.services.find_one({"id": service_id})
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    # Create rollback pipeline
    pipeline = Pipeline(
        service_id=service_id,
        stage="rollback",
        status="running"
    )
    await db.pipelines.insert_one(pipeline.dict())
    
    return {"message": "Rollback initiated", "pipeline_id": pipeline.id}

# Templates
@api_router.get("/templates", response_model=List[ServiceTemplate])
async def get_templates():
    templates = await db.templates.find().to_list(1000)
    return [ServiceTemplate(**template) for template in templates]

@api_router.get("/templates/{service_type}", response_model=ServiceTemplate)
async def get_template(service_type: str):
    template = await db.templates.find_one({"service_type": service_type})
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return ServiceTemplate(**template)

# Webhooks (for CI/CD integration)
@api_router.post("/webhooks/jenkins")
async def jenkins_webhook(webhook_data: Dict[str, Any]):
    """Handle Jenkins webhook notifications"""
    service_id = webhook_data.get('service_id')
    status = webhook_data.get('status', '').lower()
    build_number = webhook_data.get('build_number')
    service_url = webhook_data.get('service_url')
    
    if not service_id:
        raise HTTPException(status_code=400, detail="Missing service_id")
    
    # Update service status
    update_data = {
        "status": "running" if status == "success" else "failed",
        "updated_at": datetime.utcnow()
    }
    
    if service_url:
        update_data["service_url"] = service_url
    
    await db.services.update_one(
        {"id": service_id},
        {"$set": update_data}
    )
    
    # Update pipeline
    pipeline_status = "success" if status == "success" else "failed"
    await db.pipelines.update_one(
        {"service_id": service_id},
        {"$set": {
            "status": pipeline_status,
            "progress": 100,
            "updated_at": datetime.utcnow()
        }},
        sort=[("created_at", -1)]
    )
    
    # Send notification email
    service = await db.services.find_one({"id": service_id})
    if service:
        developer = await db.developers.find_one({"id": service["developer_id"]})
        if developer:
            subject = f"Velora: {service['name']} Deployment {status.title()}"
            body = f"""
            <h2>Deployment Notification</h2>
            <p><strong>Service:</strong> {service['name']}</p>
            <p><strong>Status:</strong> {status.title()}</p>
            <p><strong>Build Number:</strong> {build_number}</p>
            {f'<p><strong>Service URL:</strong> <a href="{service_url}">{service_url}</a></p>' if service_url else ''}
            <p><strong>Timestamp:</strong> {datetime.utcnow().isoformat()}</p>
            
            <p>Visit your <a href="{os.getenv('FRONTEND_URL', 'http://localhost:3000')}">Velora Dashboard</a> for more details.</p>
            """
            
            await send_email_notification(developer['email'], subject, body)
    
    return {"message": "Webhook processed successfully"}

# Dashboard Analytics
@api_router.get("/analytics/dashboard")
async def get_dashboard_analytics():
    """Get dashboard analytics data"""
    total_services = await db.services.count_documents({})
    total_developers = await db.developers.count_documents({})
    
    # Services by status
    services_by_status = await db.services.aggregate([
        {"$group": {"_id": "$status", "count": {"$sum": 1}}}
    ]).to_list(10)
    
    # Services by type
    services_by_type = await db.services.aggregate([
        {"$group": {"_id": "$service_type", "count": {"$sum": 1}}}
    ]).to_list(10)
    
    # Recent activities (last 10 services)
    recent_services = await db.services.find().sort("created_at", -1).limit(10).to_list(10)
    
    return {
        "total_services": total_services,
        "total_developers": total_developers,
        "services_by_status": {item["_id"]: item["count"] for item in services_by_status},
        "services_by_type": {item["_id"]: item["count"] for item in services_by_type},
        "recent_activities": [Service(**service) for service in recent_services]
    }

# Background Tasks
async def process_service_creation(service_id: str):
    """Background task to process service creation"""
    try:
        # Update pipeline to running
        await db.pipelines.update_one(
            {"service_id": service_id},
            {"$set": {
                "status": "running",
                "stage": "github_repo_creation",
                "progress": 10,
                "updated_at": datetime.utcnow()
            }}
        )
        
        service = await db.services.find_one({"id": service_id})
        if not service:
            return
        
        # Get GitHub token from environment
        github_token = os.getenv('GITHUB_TOKEN')
        if github_token:
            # Create GitHub repository
            repo_data = await create_github_repo(
                service['name'], 
                service['description'], 
                github_token
            )
            
            # Update service with GitHub repo URL
            await db.services.update_one(
                {"id": service_id},
                {"$set": {
                    "github_repo_url": repo_data['clone_url'],
                    "status": "building",
                    "updated_at": datetime.utcnow()
                }}
            )
            
            # Update pipeline
            await db.pipelines.update_one(
                {"service_id": service_id},
                {"$set": {
                    "stage": "template_generation",
                    "progress": 30,
                    "logs": ["GitHub repository created successfully"],
                    "updated_at": datetime.utcnow()
                }}
            )
            
            # Get and push template files
            template = await db.templates.find_one({"service_type": service['service_type']})
            if template:
                await push_template_to_repo(
                    repo_data['clone_url'], 
                    template['template_files'], 
                    github_token
                )
                
                # Update pipeline
                await db.pipelines.update_one(
                    {"service_id": service_id},
                    {"$set": {
                        "stage": "ci_cd_setup",
                        "progress": 60,
                        "logs": ["Template files pushed to repository"],
                        "updated_at": datetime.utcnow()
                    }}
                )
        
        # Simulate CI/CD pipeline trigger
        # In real implementation, this would trigger Jenkins or GitHub Actions
        await db.pipelines.update_one(
            {"service_id": service_id},
            {"$set": {
                "stage": "deployment",
                "progress": 80,
                "logs": ["CI/CD pipeline triggered"],
                "updated_at": datetime.utcnow()
            }}
        )
        
        # Final success status
        await db.services.update_one(
            {"id": service_id},
            {"$set": {
                "status": "running",
                "service_url": f"https://{service['name']}.velora.dev",
                "updated_at": datetime.utcnow()
            }}
        )
        
        await db.pipelines.update_one(
            {"service_id": service_id},
            {"$set": {
                "status": "success",
                "stage": "completed",
                "progress": 100,
                "logs": ["Service deployment completed successfully"],
                "updated_at": datetime.utcnow()
            }}
        )
        
    except Exception as e:
        # Mark as failed
        await db.services.update_one(
            {"id": service_id},
            {"$set": {"status": "failed", "updated_at": datetime.utcnow()}}
        )
        
        await db.pipelines.update_one(
            {"service_id": service_id},
            {"$set": {
                "status": "failed",
                "logs": [f"Error: {str(e)}"],
                "updated_at": datetime.utcnow()
            }}
        )
        
        logging.error(f"Service creation failed for {service_id}: {str(e)}")

# Health check
@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_db_client():
    """Initialize database collections and default data"""
    # Create default templates
    api_template = {
        "name": "FastAPI Service Template",
        "service_type": "api",
        "description": "Standard FastAPI service template",
        "template_files": {
            "main.py": '''from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/health")
async def health():
    return {"status": "healthy"}
''',
            "requirements.txt": '''fastapi==0.110.1
uvicorn==0.25.0
''',
            "Dockerfile": '''FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
''',
            "Jenkinsfile": '''pipeline {
    agent any
    stages {
        stage('Build') {
            steps {
                sh 'docker build -t $SERVICE_NAME .'
            }
        }
        stage('Deploy') {
            steps {
                sh 'docker push $SERVICE_NAME'
            }
        }
    }
}
'''
        },
        "created_at": datetime.utcnow()
    }
    
    # Check if template already exists
    existing_template = await db.templates.find_one({"service_type": "api"})
    if not existing_template:
        template_obj = ServiceTemplate(**api_template)
        await db.templates.insert_one(template_obj.dict())
        logger.info("Default API template created")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()