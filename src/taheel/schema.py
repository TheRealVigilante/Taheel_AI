"""
Domain Data Contracts and Pydantic Schemas for Taheel AI (تأهيل).

Defines the core data contracts for:
- Role profiles & organizational metadata
- SOP competency extraction (Ontology)
- 30-60-90 Day Milestone phases
- Daily 20-30 minute Micro-Action Tasks
- Manager 1-on-1 Evaluation Gates (Days 14, 30, 60, 90) aligned with Saudi Labor Law Article 53
"""

from __future__ import annotations
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, ConfigDict


class LanguageEnum(str, Enum):
    """Supported interface and output languages."""
    ARABIC = "ar"
    ENGLISH = "en"


class ComplexityEnum(str, Enum):
    """Cognitive and operational complexity rating for SOPs and tasks."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ProbationVerdictEnum(str, Enum):
    """Formal verdicts aligned with Saudi Labor Law Article 53."""
    EXCEEDS_EXPECTATIONS = "exceeds_expectations"
    ON_TRACK = "on_track"
    ACTION_PLAN_NEEDED = "action_plan_needed"
    PROBATION_RISK = "probation_risk"


# ==============================================================================
# 1. Role & Organizational Context
# ==============================================================================

class RoleProfile(BaseModel):
    """
    Profile definition of the new hire and corporate department.
    Guides the role-adaptive LLM filter to prioritize relevant SOPs.
    """
    model_config = ConfigDict(extra="ignore")

    company_name: str = Field(
        ...,
        description="Company or entity name (e.g., 'RiyadhPay Fintech' / 'راية باي')"
    )
    department: str = Field(
        ...,
        description="Target department (e.g., 'Customer Operations', 'Software Engineering')"
    )
    role_title: str = Field(
        ...,
        description="Specific position title (e.g., 'Tier-1 Customer Operations Specialist')"
    )
    mentor_name: Optional[str] = Field(
        default="Assigned Mentor",
        description="Line manager or assigned onboarding mentor"
    )
    employee_name: Optional[str] = Field(
        default="New Hire",
        description="Name of the employee being onboarded"
    )
    language: LanguageEnum = Field(
        default=LanguageEnum.ENGLISH,
        description="Primary generation and UI language ('ar' or 'en')"
    )


# ==============================================================================
# 2. Extracted SOP Competency Unit
# ==============================================================================

class SOPItem(BaseModel):
    """
    Standard Operating Procedure (SOP) competency unit extracted from manuals.
    """
    model_config = ConfigDict(extra="ignore")

    sop_id: str = Field(
        ...,
        description="Standardized code (e.g., 'SOP-OPS-001', 'SOP-SEC-012')"
    )
    title: str = Field(
        ...,
        description="Clear operational procedure title"
    )
    summary: str = Field(
        ...,
        description="Concise description of the procedure and why it matters"
    )
    target_tools: List[str] = Field(
        default_factory=list,
        description="Software systems or tools used (e.g., ['Zendesk', 'SAMA Portal', 'Admin DB'])"
    )
    complexity: ComplexityEnum = Field(
        default=ComplexityEnum.MEDIUM,
        description="Cognitive and operational complexity rating"
    )
    relevance_to_role: str = Field(
        ...,
        description="Explanation of how this procedure applies directly to the target role"
    )
    source_page_reference: Optional[str] = Field(
        default=None,
        description="Source manual page or section reference"
    )


# ==============================================================================
# 3. 30-60-90 Day Milestone Phases
# ==============================================================================

class MilestonePhase(BaseModel):
    """
    High-level milestone phase across the 90-day onboarding journey.
    - Phase 1 (Days 1-30): Learn — Tool access, safety/security, foundational workflows.
    - Phase 2 (Days 31-60): Apply — Guided execution, handling edge cases, shadowing.
    - Phase 3 (Days 61-90): Own — Independent ownership, SLAs, final probation confirmation.
    """
    model_config = ConfigDict(extra="ignore")

    phase_number: int = Field(
        ...,
        ge=1,
        le=3,
        description="Phase index: 1 (Days 1-30), 2 (Days 31-60), 3 (Days 61-90)"
    )
    phase_title: str = Field(
        ...,
        description="Descriptive title (e.g., 'Foundation & System Orientation')"
    )
    day_range: str = Field(
        ...,
        description="Standard timeline span (e.g., 'Days 1-30', 'Days 31-60', 'Days 61-90')"
    )
    core_focus: str = Field(
        ...,
        description="Primary strategic objective of this phase"
    )
    target_sops: List[SOPItem] = Field(
        default_factory=list,
        description="SOP competencies mastered during this phase"
    )


class OnboardingOntology(BaseModel):
    """
    Structured domain curriculum extracted from raw manuals,
    filtered and prioritized for the specific RoleProfile.
    """
    model_config = ConfigDict(extra="ignore")

    role_profile: RoleProfile
    identified_tools: List[str] = Field(
        default_factory=list,
        description="All tools and systems identified across relevant procedures"
    )
    phases: List[MilestonePhase] = Field(
        default_factory=list,
        description="The three 30-day milestone phases"
    )
    raw_sops_count: int = Field(
        default=0,
        description="Total number of procedures extracted"
    )


# ==============================================================================
# 4. Daily Micro-Action Cards (Cognitive Pacing CPG 2.0)
# ==============================================================================

class DailyMicroTask(BaseModel):
    """
    Daily bite-sized onboarding micro-action card capped at 20-30 minutes.
    Preserves remaining working hours for shadowing and core operational duties.
    """
    model_config = ConfigDict(extra="ignore")

    day_number: int = Field(
        ...,
        ge=1,
        le=90,
        description="Day index within the 90-day probation timeline (1 to 90)"
    )
    week_number: int = Field(
        ...,
        ge=1,
        le=13,
        description="Week index (1 to 13)"
    )
    phase_number: int = Field(
        ...,
        ge=1,
        le=3,
        description="Parent phase (1, 2, or 3)"
    )
    topic: str = Field(
        ...,
        description="Procedure or concept topic for the day"
    )
    estimated_minutes: int = Field(
        default=25,
        ge=15,
        le=45,
        description="Estimated completion time (strictly capped between 15 and 45 minutes)"
    )
    tools_needed: List[str] = Field(
        default_factory=list,
        description="Specific software or tools needed to execute today's task"
    )
    daily_mission: str = Field(
        ...,
        description="Why this matters: 1-2 sentences explaining real business impact"
    )
    sop_principles: List[str] = Field(
        default_factory=list,
        description="Key standards, compliance rules, or policy constraints"
    )
    common_mistakes_to_avoid: List[str] = Field(
        default_factory=list,
        description="Critical errors or anti-patterns to avoid"
    )
    hands_on_action_task: str = Field(
        ...,
        description="Concrete, practical simulation or action in the company's real tools"
    )
    verification_deliverable: str = Field(
        default="Documented in team ticket/notes",
        description="Tangible proof of completion"
    )
    completed: bool = Field(
        default=False,
        description="Interactive checkbox completion state"
    )


# ==============================================================================
# 5. Manager 1-on-1 Evaluation Gates (Saudi Labor Law Article 53)
# ==============================================================================

class RubricScoreItem(BaseModel):
    """Individual competency scoring item in the manager's rubric."""
    competency: str
    criterion: str
    max_score: int = 5
    assigned_score: Optional[int] = None
    manager_notes: Optional[str] = None


class ManagerEvaluationGate(BaseModel):
    """
    Formal 1-on-1 Milestone Evaluation Gate conducted by the line manager.
    Scheduled at:
    - Day 14: Early Healthcheck & Cultural Alignment
    - Day 30: Foundation & Tooling Proficiency Review
    - Day 60: Core Execution & Guided Autonomy Review
    - Day 90: Final Probation Decision Gate (Saudi Labor Law Art. 53)
    """
    model_config = ConfigDict(extra="ignore")

    gate_day: int = Field(
        ...,
        description="Milestone day: 14, 30, 60, or 90"
    )
    milestone_name: str = Field(
        ...,
        description="Descriptive milestone title (e.g., 'Early Healthcheck & Tooling Gate')"
    )
    target_phase: int = Field(
        ...,
        ge=1,
        le=3,
        description="Associated phase (1, 2, or 3)"
    )
    key_competencies_to_verify: List[str] = Field(
        ...,
        description="Concrete skills and workflows the employee must demonstrate live"
    )
    one_on_one_questions: List[str] = Field(
        ...,
        description="Probing and scenario-based interview questions for the manager"
    )
    red_flags: List[str] = Field(
        ...,
        description="Observable warning signs indicating struggle, negligence, or compliance risk"
    )
    probation_readiness_rubric: Dict[str, Any] = Field(
        default_factory=dict,
        description="Scoring rubric criteria (1-5 scale) across technical and behavioral pillars"
    )
    recommended_verdict: Optional[ProbationVerdictEnum] = Field(
        default=None,
        description="Formal manager verdict recorded for HR records"
    )
    manager_comments: Optional[str] = Field(
        default=None,
        description="Free-form manager evaluation commentary"
    )


# ==============================================================================
# 6. Master Roadmap & Package Containers
# ==============================================================================

class RoadmapWeek(BaseModel):
    """Weekly breakdown within the Master Roadmap."""
    week_number: int
    day_range: str
    phase_number: int
    theme: str
    core_sops: List[str]
    hands_on_milestone: str
    manager_checkpoint: Optional[str] = None


class MasterRoadmap(BaseModel):
    """The master 30-60-90 day schedule structured in weekly increments."""
    model_config = ConfigDict(extra="ignore")

    role_profile: RoleProfile
    weeks: List[RoadmapWeek] = Field(default_factory=list)
    markdown_content: Optional[str] = Field(
        default=None,
        description="Rendered Markdown tables for instant export or display"
    )


class OnboardingPackage(BaseModel):
    """
    Top-level container holding the complete generated onboarding ecosystem.
    Used for storage, serialization, and export bundling.
    """
    model_config = ConfigDict(extra="ignore")

    package_id: str = Field(..., description="Unique UUID for this onboarding program")
    created_at: str = Field(..., description="ISO 8601 timestamp")
    role_profile: RoleProfile
    ontology: OnboardingOntology
    roadmap: MasterRoadmap
    daily_tasks: List[DailyMicroTask] = Field(default_factory=list)
    manager_gates: List[ManagerEvaluationGate] = Field(default_factory=list)
