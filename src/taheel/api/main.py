import os
import uuid
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import FastAPI, UploadFile, Form, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.taheel.schema import (
    RoleProfile, 
    LanguageEnum,
    OnboardingPackage,
    OnboardingOntology,
    MasterRoadmap,
    DailyMicroTask,
    ManagerEvaluationGate
)
from src.taheel.ingestion.router import ingest_manual
from src.taheel.generators.ontology import OntologyGenerator
from src.taheel.generators.roadmap import RoadmapGenerator
from src.taheel.generators.daily_tasks import DailyTaskGenerator
from src.taheel.generators.manager_gates import ManagerGateGenerator
from src.taheel.pacing.cognitive_engine import CognitiveLoadBalancer
from src.taheel.exporters.notion_bundle import NotionExporter

app = FastAPI(title="Taheel AI API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory job store (for POC/MVP)
# In production, use Redis or a database
jobs: Dict[str, Dict[str, Any]] = {}

class JobStatus(BaseModel):
    job_id: str
    status: str
    progress: int
    message: str
    package: Optional[OnboardingPackage] = None

def process_onboarding_job(
    job_id: str, 
    file_path: str, 
    role_profile: RoleProfile
):
    try:
        jobs[job_id]["status"] = "processing"
        jobs[job_id]["message"] = "Ingesting document..."
        jobs[job_id]["progress"] = 10
        
        # 1. Ingestion
        doc = ingest_manual(file_path)
        raw_text = doc.full_text
        
        jobs[job_id]["message"] = "Generating Ontology..."
        jobs[job_id]["progress"] = 30
        
        # 2. Ontology
        ontology_gen = OntologyGenerator()
        ontology = ontology_gen.generate(raw_text, role_profile)
        
        jobs[job_id]["message"] = "Generating Master Roadmap..."
        jobs[job_id]["progress"] = 50
        
        # 3. Roadmap
        roadmap_gen = RoadmapGenerator()
        roadmap = roadmap_gen.generate(ontology)
        
        jobs[job_id]["message"] = "Distributing SOPs & Generating Tasks..."
        jobs[job_id]["progress"] = 70
        
        # 4. Pacing & Daily Tasks
        balancer = CognitiveLoadBalancer(ontology)
        weekly_schedule = balancer.distribute_sops_to_weeks()
        
        task_gen = DailyTaskGenerator()
        daily_tasks = []
        current_day = 1
        
        for week_num, sops in weekly_schedule.items():
            # Determine phase from week (approximate)
            if week_num <= 4:
                phase_num = 1
            elif week_num <= 8:
                phase_num = 2
            else:
                phase_num = 3
                
            for sop in sops:
                # Basic pacing: 1 SOP per day for simplicity in the POC
                task = task_gen.generate(
                    day_number=current_day,
                    week_number=week_num,
                    phase_number=phase_num,
                    sop=sop,
                    role_profile=role_profile
                )
                daily_tasks.append(task)
                current_day += 1

        jobs[job_id]["message"] = "Generating Manager Evaluation Gates..."
        jobs[job_id]["progress"] = 85
                
        # 5. Manager Gates
        gate_gen = ManagerGateGenerator()
        manager_gates = []
        gate_days = {
            14: ("Early Healthcheck", 1),
            30: ("Foundation Review", 1),
            60: ("Execution Review", 2),
            90: ("Final Probation Decision Gate", 3)
        }
        
        for day, (name, target_phase) in gate_days.items():
            # Find the matching phase from ontology to pass to the generator
            phase_data = next((p for p in ontology.phases if p.phase_number == target_phase), None)
            if phase_data:
                gate = gate_gen.generate(
                    gate_day=day,
                    milestone_name=name,
                    target_phase=target_phase,
                    phase_data=phase_data,
                    role_profile=role_profile
                )
                manager_gates.append(gate)
                
        # 6. Package Assembly
        jobs[job_id]["message"] = "Assembling Final Package..."
        jobs[job_id]["progress"] = 95
        
        package = OnboardingPackage(
            package_id=job_id,
            created_at=datetime.utcnow().isoformat(),
            role_profile=role_profile,
            ontology=ontology,
            roadmap=roadmap,
            daily_tasks=daily_tasks,
            manager_gates=manager_gates
        )
        
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["progress"] = 100
        jobs[job_id]["message"] = "Processing complete."
        jobs[job_id]["package"] = package
        
    except Exception as e:
        jobs[job_id]["status"] = "error"
        jobs[job_id]["message"] = f"Failed: {str(e)}"
    finally:
        # Cleanup temp file
        if os.path.exists(file_path):
            os.remove(file_path)

@app.post("/api/v1/jobs", response_model=JobStatus)
async def create_job(
    background_tasks: BackgroundTasks,
    document: UploadFile,
    company_name: str = Form(...),
    department: str = Form(...),
    role_title: str = Form(...),
    mentor_name: str = Form("Assigned Mentor"),
    language: str = Form("en")
):
    job_id = str(uuid.uuid4())
    
    # Save uploaded file to temp path
    suffix = Path(document.filename).suffix
    with NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        content = await document.read()
        temp_file.write(content)
        temp_file_path = temp_file.name
        
    role_profile = RoleProfile(
        company_name=company_name,
        department=department,
        role_title=role_title,
        mentor_name=mentor_name,
        language=LanguageEnum.ARABIC if language == "ar" else LanguageEnum.ENGLISH
    )
    
    jobs[job_id] = {
        "status": "pending",
        "progress": 0,
        "message": "Job queued.",
        "package": None
    }
    
    background_tasks.add_task(process_onboarding_job, job_id, temp_file_path, role_profile)
    
    return JobStatus(job_id=job_id, **jobs[job_id])

@app.get("/api/v1/jobs/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return JobStatus(job_id=job_id, **jobs[job_id])

@app.get("/api/v1/jobs/{job_id}/export")
async def export_job_zip(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
        
    job = jobs[job_id]
    if job["status"] != "completed" or not job["package"]:
        raise HTTPException(status_code=400, detail="Job is not completed yet")
        
    package: OnboardingPackage = job["package"]
    zip_buffer = NotionExporter.generate_zip_bundle(package)
    
    headers = {
        "Content-Disposition": f"attachment; filename={package.role_profile.role_title.replace(' ', '_').lower()}_onboarding.zip"
    }
    
    return StreamingResponse(
        iter([zip_buffer.getvalue()]), 
        media_type="application/zip",
        headers=headers
    )
