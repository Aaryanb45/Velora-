from fastapi import FastAPI, APIRouter, HTTPException, BackgroundTasks
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone
from enum import Enum
import asyncio
import random

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(title="Velora API", description="Internal Developer Platform API")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Enums
class ServiceStatus(str, Enum):
    CREATING = "creating"
    BUILDING = "building"
    DEPLOYING = "deploying"
    RUNNING = "running"
    FAILED = "failed"
    STOPPED = "stopped"

class PipelineStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"

class ServiceType(str, Enum):
    API = "api"
    FRONTEND = "frontend"
    WORKER = "worker"
    DATABASE = "database"

# Models
class Developer(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    email: str
    github_username: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    services_count: int = 0
    last_activity: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class DeveloperCreate(BaseModel):
    name: str
    email: str
    github_username: str

class Service(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    service_type: ServiceType
    developer_id: str
    status: ServiceStatus = ServiceStatus.CREATING
    github_repo_url: Optional[str] = None
    service_url: Optional[str] = None
    docker_image: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    pods_running: int = 0
    pods_desired: int = 1

class ServiceCreate(BaseModel):
    name: str
    description: str
    service_type: ServiceType
    developer_id: str

class Pipeline(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    service_id: str
    status: PipelineStatus = PipelineStatus.PENDING
    stage: str = "Code Analysis"
    progress: int = 0
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    logs: List[str] = []

class PipelineStep(BaseModel):
    name: str
    status: PipelineStatus
    duration: Optional[int] = None
    logs: List[str] = []

class MetricsData(BaseModel):
    timestamp: datetime
    cpu_usage: float
    memory_usage: float
    requests_per_minute: int

class ClusterStats(BaseModel):
    total_services: int
    running_services: int
    failed_services: int
    total_pods: int
    total_developers: int
    cpu_utilization: float
    memory_utilization: float
    cost_this_month: float

# Helper functions
async def simulate_pipeline(service_id: str, service_name: str):
    """Simulate pipeline execution"""
    pipeline = Pipeline(service_id=service_id)
    await db.pipelines.insert_one(pipeline.dict())
    
    stages = [
        ("Code Analysis", 15),
        ("Docker Build", 30),
        ("Security Scan", 45),
        ("Push to Registry", 60),
        ("Deploy to K8s", 80),
        ("Health Check", 100)
    ]
    
    for stage_name, progress in stages:
        await asyncio.sleep(2)  # Simulate processing time
        pipeline.stage = stage_name
        pipeline.progress = progress
        pipeline.logs.append(f"✓ {stage_name} completed successfully")
        
        if progress == 100:
            pipeline.status = PipelineStatus.SUCCESS
            pipeline.completed_at = datetime.now(timezone.utc)
            
            # Update service status
            await db.services.update_one(
                {"id": service_id},
                {
                    "$set": {
                        "status": ServiceStatus.RUNNING,
                        "service_url": f"https://{service_name.lower().replace(' ', '-')}.velora.dev",
                        "github_repo_url": f"https://github.com/developer/{service_name.lower().replace(' ', '-')}",
                        "docker_image": f"velora/{service_name.lower().replace(' ', '-')}:latest",
                        "pods_running": random.randint(1, 3),
                        "cpu_usage": round(random.uniform(10, 80), 1),
                        "memory_usage": round(random.uniform(20, 70), 1),
                        "updated_at": datetime.now(timezone.utc)
                    }
                }
            )
        else:
            pipeline.status = PipelineStatus.RUNNING
            
        await db.pipelines.update_one(
            {"id": pipeline.id},
            {"$set": pipeline.dict()}
        )

# API Routes
@api_router.get("/")
async def root():
    return {"message": "Velora API - Internal Developer Platform"}

# Developer routes
@api_router.post("/developers", response_model=Developer)
async def create_developer(developer_data: DeveloperCreate):
    developer = Developer(**developer_data.dict())
    await db.developers.insert_one(developer.dict())
    return developer

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

# Service routes
@api_router.post("/services", response_model=Service)
async def create_service(service_data: ServiceCreate, background_tasks: BackgroundTasks):
    service = Service(**service_data.dict())
    await db.services.insert_one(service.dict())
    
    # Update developer's service count
    await db.developers.update_one(
        {"id": service_data.developer_id},
        {
            "$inc": {"services_count": 1},
            "$set": {"last_activity": datetime.now(timezone.utc)}
        }
    )
    
    # Start pipeline simulation in background
    background_tasks.add_task(simulate_pipeline, service.id, service.name)
    
    return service

@api_router.get("/services", response_model=List[Service])
async def get_services(developer_id: Optional[str] = None):
    query = {"developer_id": developer_id} if developer_id else {}
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
    return {"message": "Service deleted successfully"}

@api_router.post("/services/{service_id}/rollback")
async def rollback_service(service_id: str):
    service = await db.services.find_one({"id": service_id})
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    # Simulate rollback
    await db.services.update_one(
        {"id": service_id},
        {
            "$set": {
                "status": ServiceStatus.DEPLOYING,
                "updated_at": datetime.now(timezone.utc)
            }
        }
    )
    
    # Simulate rollback completion after 3 seconds
    await asyncio.sleep(3)
    await db.services.update_one(
        {"id": service_id},
        {
            "$set": {
                "status": ServiceStatus.RUNNING,
                "updated_at": datetime.now(timezone.utc)
            }
        }
    )
    
    return {"message": "Rollback initiated successfully"}

# Pipeline routes
@api_router.get("/services/{service_id}/pipeline", response_model=Pipeline)
async def get_service_pipeline(service_id: str):
    pipeline = await db.pipelines.find_one({"service_id": service_id})
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    return Pipeline(**pipeline)

# Metrics routes
@api_router.get("/services/{service_id}/metrics")
async def get_service_metrics(service_id: str):
    # Generate mock metrics data
    metrics = []
    for i in range(24):  # 24 hours of data
        metrics.append({
            "timestamp": datetime.now(timezone.utc).replace(hour=i, minute=0, second=0),
            "cpu_usage": round(random.uniform(10, 80), 1),
            "memory_usage": round(random.uniform(20, 70), 1),
            "requests_per_minute": random.randint(50, 500)
        })
    return metrics

@api_router.get("/services/{service_id}/logs")
async def get_service_logs(service_id: str):
    # Generate mock logs
    log_levels = ["INFO", "WARN", "ERROR", "DEBUG"]
    logs = []
    for i in range(50):
        logs.append({
            "timestamp": datetime.now(timezone.utc),
            "level": random.choice(log_levels),
            "message": f"Application log entry {i+1} - Service processing request"
        })
    return logs

# Admin routes
@api_router.get("/admin/stats", response_model=ClusterStats)
async def get_cluster_stats():
    total_services = await db.services.count_documents({})
    running_services = await db.services.count_documents({"status": ServiceStatus.RUNNING})
    failed_services = await db.services.count_documents({"status": ServiceStatus.FAILED})
    total_developers = await db.developers.count_documents({})
    
    # Mock additional stats
    total_pods = await db.services.aggregate([
        {"$group": {"_id": None, "total": {"$sum": "$pods_running"}}}
    ]).to_list(1)
    
    stats = ClusterStats(
        total_services=total_services,
        running_services=running_services,
        failed_services=failed_services,
        total_pods=total_pods[0]["total"] if total_pods else 0,
        total_developers=total_developers,
        cpu_utilization=round(random.uniform(40, 80), 1),
        memory_utilization=round(random.uniform(50, 75), 1),
        cost_this_month=round(random.uniform(1000, 5000), 2)
    )
    return stats

@api_router.get("/admin/developers-activity")
async def get_developers_activity():
    # Get developers with their service counts and last activity
    pipeline = [
        {
            "$lookup": {
                "from": "services",
                "localField": "id",
                "foreignField": "developer_id",
                "as": "services"
            }
        },
        {
            "$project": {
                "name": 1,
                "email": 1,
                "github_username": 1,
                "created_at": 1,
                "last_activity": 1,
                "services_count": {"$size": "$services"},
                "running_services": {
                    "$size": {
                        "$filter": {
                            "input": "$services",
                            "cond": {"$eq": ["$$this.status", "running"]}
                        }
                    }
                }
            }
        }
    ]
    
    developers = await db.developers.aggregate(pipeline).to_list(1000)
    return developers

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

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()