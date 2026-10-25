"""
Stepwise Pipeline Orchestration API for Taheel AI (تأهيل).

Instead of generating the whole onboarding package in one long-running job,
each part is generated as an explicit, separately triggered step:

    1. ingest   - document ingestion (runs automatically at job creation)
    2. ontology - role-adaptive ontology extraction        (POST /steps/ontology)
    3. roadmap  - master 30-60-90 roadmap                  (POST /steps/roadmap)
    4. tasks    - daily micro-task cards                   (POST /steps/tasks)
    5. gates    - manager evaluation gates + final package (POST /steps/gates)

The job pauses in "ready" state after each step until the client asks for
the next one. A failed step can be retried individually.
"""

import os
import uuid
import time
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import FastAPI, UploadFile, Form, BackgroundTasks, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

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

app = FastAPI(title="Taheel AI API", version="1.1.0")

logger = logging.getLogger("taheel.api")

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

# Sequential pipeline steps. "ingest" runs automatically when the job is
# created; each following step must be triggered explicitly, one at a time.
STEP_ORDER = ["ingest", "ontology", "roadmap", "tasks", "gates"]
STEP_LABELS = {
    "ingest": "Document Ingestion",
    "ontology": "Role-Adaptive Ontology",
    "roadmap": "Master 30-60-90 Roadmap",
    "tasks": "Daily Micro-Tasks",
    "gates": "Manager Evaluation Gates",
}
# Overall pipeline progress (0-100) once each step has completed
STEP_COMPLETION_PROGRESS = {
    "ingest": 20,
    "ontology": 40,
    "roadmap": 60,
    "tasks": 80,
    "gates": 100,
}


class JobStatus(BaseModel):
    job_id: str
    status: str  # processing | ready | completed | error
    current_step: Optional[str] = None
    next_step: Optional[str] = None
    steps_done: List[str] = Field(default_factory=list)
    progress: int
    message: str
    ontology: Optional[OnboardingOntology] = None
    roadmap: Optional[MasterRoadmap] = None
    daily_tasks: Optional[List[DailyMicroTask]] = None
    manager_gates: Optional[List[ManagerEvaluationGate]] = None
    package: Optional[OnboardingPackage] = None


def _job_status(job_id: str) -> JobStatus:
    """Builds the API response view of a job (hides internal fields like temp paths)."""
    job = jobs[job_id]
    return JobStatus(
        job_id=job_id,
        status=job["status"],
        current_step=job.get("current_step"),
        next_step=job.get("next_step"),
        steps_done=job.get("steps_done", []),
        progress=job["progress"],
        message=job["message"],
        ontology=job.get("ontology"),
        roadmap=job.get("roadmap"),
        daily_tasks=job.get("daily_tasks"),
        manager_gates=job.get("manager_gates"),
        package=job.get("package"),
    )


def _finish_step(job_id: str, step: str) -> None:
    """Marks a step as complete and pauses the job, waiting for the next trigger."""
    job = jobs[job_id]
    if step not in job["steps_done"]:
        job["steps_done"].append(step)
    job["progress"] = STEP_COMPLETION_PROGRESS[step]
    job["current_step"] = None
    if step == "gates":
        job["status"] = "completed"
        job["next_step"] = None
        job["message"] = "Pipeline complete. All parts generated."
    else:
        next_step = STEP_ORDER[STEP_ORDER.index(step) + 1]
        job["status"] = "ready"
        job["next_step"] = next_step
        job["message"] = f"{STEP_LABELS[step]} complete. Next: {STEP_LABELS[next_step]}."


def _fail_step(job_id: str, step: str, exc: Exception) -> None:
    """Marks the current step as failed. The same step can be retried later."""
    job = jobs[job_id]
    job["status"] = "error"
    job["message"] = f"{STEP_LABELS[step]} failed: {exc}"


def _assemble_package(job_id: str) -> None:
    """Assembles the final OnboardingPackage from all generated artifacts."""
    job = jobs[job_id]
    job["package"] = OnboardingPackage(
        package_id=job_id,
        created_at=datetime.utcnow().isoformat(),
        role_profile=job["role_profile"],
        ontology=job["ontology"],
        roadmap=job["roadmap"],
        daily_tasks=job["daily_tasks"] or [],
        manager_gates=job["manager_gates"] or [],
    )


# ---------------------------------------------------------------------------
# Step runners (executed as background tasks, exactly one step at a time)
# ---------------------------------------------------------------------------

def run_ingest_step(job_id: str, file_path: str) -> None:
    """Step 1: extracts and cleans the raw manual text."""
    job = jobs[job_id]
    logger.info("[%s] ► STEP: ingest | Starting document ingestion...", job_id[:8])
    t0 = time.perf_counter()
    try:
        job["message"] = "Ingesting document..."
        doc = ingest_manual(file_path)
        job["raw_text"] = doc.full_text
        # Raw text is now stored; the temporary upload is no longer needed.
        job["file_path"] = None
        try:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
        except OSError:
            pass
        logger.info(
            "[%s] ✔ STEP ingest done in %.1fs | extracted %d chars.",
            job_id[:8], time.perf_counter() - t0, len(job["raw_text"])
        )
        _finish_step(job_id, "ingest")
    except Exception as e:
        logger.error("[%s] ✘ STEP ingest FAILED in %.1fs: %s", job_id[:8], time.perf_counter() - t0, e)
        # Keep the temp file so the ingest step can be retried.
        _fail_step(job_id, "ingest", e)


def run_ontology_step(job_id: str) -> None:
    """Step 2: extracts the role-adaptive competency ontology from the raw text."""
    job = jobs[job_id]
    logger.info("[%s] ► STEP: ontology | Generating role-adaptive ontology...", job_id[:8])
    t0 = time.perf_counter()
    try:
        job["progress"] = 30
        job["message"] = "Generating ontology..."
        job["ontology"] = OntologyGenerator().generate(job["raw_text"], job["role_profile"])
        logger.info("[%s] ✔ STEP ontology done in %.1fs.", job_id[:8], time.perf_counter() - t0)
        _finish_step(job_id, "ontology")
    except Exception as e:
        logger.error("[%s] ✘ STEP ontology FAILED in %.1fs: %s", job_id[:8], time.perf_counter() - t0, e)
        _fail_step(job_id, "ontology", e)


def run_roadmap_step(job_id: str) -> None:
    """Step 3: builds the master 13-week 30-60-90 roadmap from the ontology."""
    job = jobs[job_id]
    logger.info("[%s] ► STEP: roadmap | Generating master 30-60-90 roadmap...", job_id[:8])
    t0 = time.perf_counter()
    try:
        job["progress"] = 50
        job["message"] = "Generating master roadmap..."
        job["roadmap"] = RoadmapGenerator().generate(job["ontology"])
        logger.info("[%s] ✔ STEP roadmap done in %.1fs.", job_id[:8], time.perf_counter() - t0)
        _finish_step(job_id, "roadmap")
    except Exception as e:
        logger.error("[%s] ✘ STEP roadmap FAILED in %.1fs: %s", job_id[:8], time.perf_counter() - t0, e)
        _fail_step(job_id, "roadmap", e)


def run_tasks_step(job_id: str) -> None:
    """Step 4: paces the SOPs across weeks and generates one task card per SOP."""
    job = jobs[job_id]
    logger.info("[%s] ► STEP: tasks | Distributing SOPs and generating task cards...", job_id[:8])
    t0 = time.perf_counter()
    try:
        job["message"] = "Distributing SOPs across weeks..."
        balancer = CognitiveLoadBalancer(job["ontology"])
        weekly_schedule = balancer.distribute_sops_to_weeks()

        task_gen = DailyTaskGenerator()
        daily_tasks: List[DailyMicroTask] = []
        current_day = 1
        total_sops = sum(len(sops) for sops in weekly_schedule.values())
        processed = 0
        logger.info("[%s] tasks | %d SOPs to generate across %d weeks.", job_id[:8], total_sops, len(weekly_schedule))

        for week_num, sops in weekly_schedule.items():
            # Determine phase from week (approximate)
            if week_num <= 4:
                phase_num = 1
            elif week_num <= 8:
                phase_num = 2
            else:
                phase_num = 3

            for sop in sops:
                processed += 1
                job["message"] = f"Generating daily task {processed}/{total_sops}: {sop.title}..."
                job["progress"] = 60 + int(20 * processed / max(total_sops, 1))
                logger.info(
                    "[%s] tasks | [%d/%d] Wk%d/Ph%d — '%s'",
                    job_id[:8], processed, total_sops, week_num, phase_num, sop.title
                )
                # Basic pacing: 1 SOP per day for simplicity in the POC
                task = task_gen.generate(
                    day_number=current_day,
                    week_number=week_num,
                    phase_number=phase_num,
                    sop=sop,
                    role_profile=job["role_profile"]
                )
                daily_tasks.append(task)
                current_day += 1

        job["daily_tasks"] = daily_tasks
        logger.info("[%s] ✔ STEP tasks done in %.1fs | %d task cards generated.",
                    job_id[:8], time.perf_counter() - t0, len(daily_tasks))
        _finish_step(job_id, "tasks")
    except Exception as e:
        logger.error("[%s] ✘ STEP tasks FAILED in %.1fs: %s", job_id[:8], time.perf_counter() - t0, e)
        _fail_step(job_id, "tasks", e)


def run_gates_step(job_id: str) -> None:
    """Step 5: generates the manager evaluation gates and assembles the final package."""
    job = jobs[job_id]
    logger.info("[%s] ► STEP: gates | Generating manager evaluation gates...", job_id[:8])
    t0 = time.perf_counter()
    try:
        gate_gen = ManagerGateGenerator()
        manager_gates: List[ManagerEvaluationGate] = []
        gate_days = {
            14: ("Early Healthcheck", 1),
            30: ("Foundation Review", 1),
            60: ("Execution Review", 2),
            90: ("Final Probation Decision Gate", 3)
        }

        total = len(gate_days)
        processed = 0
        for day, (name, target_phase) in gate_days.items():
            processed += 1
            job["message"] = f"Generating manager gate {processed}/{total}: Day {day} {name}..."
            job["progress"] = 80 + int(20 * processed / total)
            logger.info(
                "[%s] gates | [%d/%d] Day %d — '%s' (phase %d)",
                job_id[:8], processed, total, day, name, target_phase
            )
            # Find the matching phase from ontology to pass to the generator
            phase_data = next((p for p in job["ontology"].phases if p.phase_number == target_phase), None)
            if phase_data:
                gate = gate_gen.generate(
                    gate_day=day,
                    milestone_name=name,
                    target_phase=target_phase,
                    phase_data=phase_data,
                    role_profile=job["role_profile"]
                )
                manager_gates.append(gate)

        job["manager_gates"] = manager_gates
        _assemble_package(job_id)
        logger.info("[%s] ✔ STEP gates done in %.1fs | %d gates generated.",
                    job_id[:8], time.perf_counter() - t0, len(manager_gates))
        _finish_step(job_id, "gates")
    except Exception as e:
        logger.error("[%s] ✘ STEP gates FAILED in %.1fs: %s", job_id[:8], time.perf_counter() - t0, e)
        _fail_step(job_id, "gates", e)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

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
        "status": "processing",
        "current_step": "ingest",
        "next_step": None,
        "steps_done": [],
        "progress": 5,
        "message": "Job queued. Ingesting document...",
        "file_path": temp_file_path,
        "raw_text": None,
        "role_profile": role_profile,
        "ontology": None,
        "roadmap": None,
        "daily_tasks": None,
        "manager_gates": None,
        "package": None,
    }

    # Ingestion starts immediately (no LLM involved);
    # every later step is triggered individually via /steps/{step}.
    background_tasks.add_task(run_ingest_step, job_id, temp_file_path)

    return _job_status(job_id)


@app.post("/api/v1/jobs/{job_id}/steps/{step}", response_model=JobStatus)
async def run_step(job_id: str, step: str, background_tasks: BackgroundTasks):
    """Runs exactly one pipeline step. Steps must be executed in order."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    if step not in STEP_ORDER:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown step '{step}'. Valid steps: {', '.join(STEP_ORDER)}"
        )

    job = jobs[job_id]

    if job["status"] == "processing":
        raise HTTPException(
            status_code=409,
            detail=f"Step '{job['current_step']}' is already running"
        )
    if job["status"] == "completed":
        raise HTTPException(status_code=400, detail="All steps are already completed")
    if job["status"] == "error":
        if job["current_step"] != step:
            raise HTTPException(
                status_code=409,
                detail=f"Step '{job['current_step']}' failed. Retry that step before moving on."
            )
    elif step != job["next_step"]:
        raise HTTPException(
            status_code=409,
            detail=f"Step '{step}' cannot run yet. Next expected step: '{job['next_step']}'."
        )

    job["status"] = "processing"
    job["current_step"] = step
    job["message"] = f"Running {STEP_LABELS[step]}..."

    step_runners = {
        "ingest": (run_ingest_step, (job_id, job["file_path"])),
        "ontology": (run_ontology_step, (job_id,)),
        "roadmap": (run_roadmap_step, (job_id,)),
        "tasks": (run_tasks_step, (job_id,)),
        "gates": (run_gates_step, (job_id,)),
    }
    runner, args = step_runners[step]
    background_tasks.add_task(runner, *args)

    return _job_status(job_id)


@app.get("/api/v1/jobs/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    return _job_status(job_id)


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
