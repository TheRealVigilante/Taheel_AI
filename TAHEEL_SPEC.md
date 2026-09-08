# 🚀 Taheel AI (تأهيل) — Master Architecture & Product Specification

> **Enterprise 30-60-90 Day Employee Onboarding & Probation Governance Engine**  
> *Bilingual (Arabic & English) | Aligned with Saudi Labor Law (Article 53) | Role-Adaptive AI*

---

## 1. Executive Summary & Vision

**Taheel AI (نظام التأهيل الذكي)** transforms dense, unstructured corporate handbooks, standard operating procedures (SOPs), and operational manuals into a personalized, role-adaptive **30-60-90 Day Onboarding & Probation Mastery System**.

### The Core Business Problem
- **The Probation Blindspot:** Under **Article 53 of the Saudi Labor Law**, employers and employees have **90 days** to evaluate mutual fit. Most companies lack a structured daily framework, resulting in subjective, stressful, and rushed decisions at Day 85.
- **Cognitive Overload:** New hires are given 300+ pages of wikis and PDFs in Week 1, leading to burnout, low retention, and prolonged time-to-productivity.
- **Manager Time Poverty:** Line managers do not have 40+ hours to write tailored day-by-day training plans, daily drills, and structured 1-on-1 evaluation rubrics.

### The Taheel AI Solution
1. **Multi-Modal Ingestion:** Ingests company manuals (PDF/Text, English and Arabic) with OCR and RTL text normalization.
2. **Role-Adaptive Personalization:** Tailors the training path to the new hire’s specific role (e.g., *Customer Operations Specialist*, *Junior Software Engineer*, *Account Executive*).
3. **Cognitive Load Pacing (CPG 2.0):** Mathematically balances learning to 20–30 minutes per day, preserving the remaining working hours for shadowing and core job duties.
4. **Hybrid Delivery Model:**
   - **Interactive Web Dashboard:** Progress stepper, daily task checklists, and manager evaluation cards.
   - **Exportable Packages:** Instant one-click export to **Notion-ready templates**, clean **Markdown**, and complete `.zip` archives.
5. **Two-Sided Governance:**
   - **Employee Layer:** Simple daily micro-action checklist (Mission $\rightarrow$ SOP Rule $\rightarrow$ Practical Task $\rightarrow$ Checkbox).
   - **Manager Layer:** Structured 1-on-1 milestone review rubrics at **Days 14, 30, 60, and 90** with formal probation pass/risk scoring.

---

## 2. Regulatory & Market Alignment (Saudi Arabia & MENA)

| Framework / Regulation | How Taheel AI Aligns |
| :--- | :--- |
| **Saudi Labor Law Article 53 (فترة التجربة)** | The entire curriculum is structured around the 90-day probation window, with formal evaluation gates at Days 14 (Early Healthcheck), 30 (Foundation), 60 (Execution), and 90 (Probation Decision). |
| **Tamheer & HRDF (تمهير / صندوق هدف)** | Generates formal, audit-ready training milestone plans required for fresh graduate on-the-job training compliance. |
| **Vision 2030 Human Capability Development** | Bridges the transition from theoretical knowledge to practical corporate operational competency. |
| **Bilingual Corporate Reality** | Supports full Arabic text extraction, Arabic prompt synthesis, and side-by-side English/Arabic outputs for multinational and local teams. |

---

## 3. Clean Target Architecture for New Repository (`Taheel_AI`)

```text
Taheel_AI/
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
├── TAHEEL_SPEC.md                      <-- This specification
├── IMPLEMENTATION_PLAN.md              <-- Technical execution plan
├── data/
│   ├── sample_sops/                    <-- Mock bilingual company SOPs for instant testing
│   │   └── fintech_customer_ops_sop.md
│   └── outputs/                        <-- Generated roadmaps & packages
└── src/
    └── taheel/
        ├── __init__.py
        ├── schema.py                   <-- Strict Pydantic domain models
        ├── ingestion/
        │   ├── __init__.py
        │   ├── pdf_engine.py           <-- Multi-engine OCR (PyMuPDF + EasyOCR + LLM Vision)
        │   └── arabic_cleaner.py       <-- Arabic normalization, RTL, and encoding fixes
        ├── pacing/
        │   ├── __init__.py
        │   └── cognitive_engine.py     <-- Cognitive load balancer (20-30 min/day caps)
        ├── generators/
        │   ├── __init__.py
        │   ├── ontology.py             <-- Role-adaptive SOP competency extractor
        │   ├── roadmap.py              <-- Master 30-60-90 Day Roadmap generator
        │   ├── daily_tasks.py          <-- Daily micro-action cards & checkboxes
        │   └── manager_gates.py        <-- Days 14, 30, 60, 90 1-on-1 review rubrics
        ├── exporters/
        │   ├── __init__.py
        │   └── notion_bundle.py        <-- Notion callout/toggle & Markdown zip packager
        ├── api/
        │   ├── __init__.py
        │   └── main.py                 <-- FastAPI async pipeline endpoints
        └── ui/
            └── app.py                  <-- Streamlit enterprise onboarding portal
```

---

## 4. Core Pydantic Data Contracts (`schema.py`)

```python
from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

class LanguageEnum(str, Enum):
    ARABIC = "ar"
    ENGLISH = "en"

class RoleProfile(BaseModel):
    company_name: str = Field(..., description="e.g. RiyadhPay Fintech")
    department: str = Field(..., description="e.g. Customer Operations")
    role_title: str = Field(..., description="e.g. Tier-1 Support Specialist")
    mentor_name: Optional[str] = Field("Assigned Mentor", description="Manager/Mentor name")
    language: LanguageEnum = Field(LanguageEnum.ENGLISH, description="Primary output language")

class SOPItem(BaseModel):
    sop_id: str
    title: str
    summary: str
    target_tools: List[str]
    complexity: str  # low, medium, high, critical
    relevance_to_role: str

class MilestonePhase(BaseModel):
    phase_number: int  # 1 (Days 1-30), 2 (Days 31-60), 3 (Days 61-90)
    phase_title: str   # e.g., "Foundation & System Orientation"
    day_range: str     # "Days 1-30"
    core_focus: str
    target_sops: List[SOPItem]

class DailyMicroTask(BaseModel):
    day_number: int
    week_number: int
    phase_number: int
    topic: str
    estimated_minutes: int = Field(25, ge=15, le=45)
    daily_mission: str
    sop_principles: List[str]
    common_mistakes_to_avoid: List[str]
    hands_on_action_task: str
    completed: bool = False

class ManagerEvaluationGate(BaseModel):
    gate_day: int  # 14, 30, 60, or 90
    milestone_name: str
    key_competencies_to_verify: List[str]
    one_on_one_questions: List[str]
    red_flags: List[str]
    probation_readiness_rubric: dict
```

---

## 5. Master LLM System Prompts

### Prompt 1: Role-Adaptive Ontology Extraction (`generators/ontology.py`)
```text
You are an expert Enterprise Workforce Enablement Architect.
Analyze the provided company manual/SOP documentation and extract an onboarding competency framework tailored specifically for:

Target Role: {role_title}
Department: {department}
Company: {company_name}
Language: {language}

INSTRUCTIONS:
1. Filter out procedures that are irrelevant to this specific role (e.g., ignore low-level code deployment if onboarding a Customer Success Rep).
2. Group the relevant competencies into the standard 3-phase journey:
   - Phase 1 (Days 1-30): Learn — Tool access, safety/security compliance, essential daily workflows.
   - Phase 2 (Days 31-60): Apply — Guided task execution, handling common edge cases, shadow sessions.
   - Phase 3 (Days 61-90): Own — Independent resolution, SLA compliance, cross-team escalation, probation readiness.
3. For each SOP, extract the key software/tools used and identify common operational mistakes.

Return ONLY a valid JSON matching the OnboardingOntology schema.
```

### Prompt 2: Master 30-60-90 Day Roadmap (`generators/roadmap.py`)
```text
You are an Executive HR & Operations Director.
Create the Master 30-60-90 Day Onboarding Roadmap for {role_title} at {company_name}.

The roadmap must be formatted as clean Markdown tables divided into:
- Phase 1: Days 1 to 30 (Foundation & Orientation)
- Phase 2: Days 31 to 60 (Core Execution & Guided Autonomy)
- Phase 3: Days 61 to 90 (Full Ownership & Final Probation Assessment)

Each table must have the following exact columns:
| Week | Day Range | Core SOPs / Topics | Hands-On Milestone Task | Manager Gate / Checkpoint |

Rules:
- Week 2 must end with the "Day 14 Early Healthcheck Gate".
- Week 4 must end with the "Day 30 Foundation Review".
- Week 8 must end with the "Day 60 Execution Review".
- Week 12 must end with the "Day 90 Final Probation Decision Gate (Saudi Labor Law Art. 53)".
```

### Prompt 3: Daily Micro-Action Cards (`generators/daily_tasks.py`)
```text
You are a Senior Operational Mentor.
Generate a structured Daily Micro-Action Onboarding Card for:
Day #: {day_number} | Week #: {week_number} | Role: {role_title}
Topic / SOP: {topic}

MANDATORY OUTPUT FORMAT (Markdown):

### ☀️ Day {day_number}: {topic}
⏱️ **Estimated Time:** 25 minutes | 🏢 **Tools Needed:** {tools}

#### 1. Daily Mission (Why this matters)
{1-2 sentences explaining business impact}

#### 2. Core SOP Rules & Standards
- {Rule 1 from document}
- {Rule 2 from document}
- ⚠️ **Common Mistake to Avoid:** {specific pitfall}

#### 3. Hands-On Workplace Task (15 mins)
{Step-by-step concrete simulation or action in the company's real software}

#### 4. Progress Checkbox
- [ ] Task executed and verified
- [ ] Documented in team notes / ticket attached
```

### Prompt 4: Manager 1-on-1 Evaluation Gates (`generators/manager_gates.py`)
```text
You are a Chief People Officer and Legal Compliance Specialist.
Generate the formal Manager 1-on-1 Evaluation Rubric for:
Milestone: Day {gate_day} ({milestone_name})
Role: {role_title} | Department: {department}

FORMAT:
# 🛡️ Manager Milestone Evaluation: Day {gate_day}
**Employee:** {employee_name} | **Manager:** {mentor_name} | **Date:** {date}

### 1. Verification Checklist (What the employee must demonstrate)
- [ ] {Competency 1}
- [ ] {Competency 2}

### 2. Guided 1-on-1 Interview Questions
1. "{Targeted question to probe deep understanding of company SOP}"
2. "{Scenario question: 'How would you handle situation X?'}"

### 3. Red Flags to Watch For
- 🚩 {Observable warning sign indicating struggle or compliance risk}

### 4. Saudi Labor Law Article 53 Probation Verdict
- [ ] **Exceeds Expectations** — Fast-track to advanced projects
- [ ] **On Track** — Proceed to next milestone
- [ ] **Action Plan Needed** — Specific 14-day remediation
- [ ] **Probation Risk / Do Not Confirm** — Formal HR escalation
```

---

## 6. How to Bootstrap the New Project

```powershell
# 1. Clone or create the new directory
mkdir C:\Users\themi\PycharmProjects\Taheel_AI
cd C:\Users\themi\PycharmProjects\Taheel_AI

# 2. Copy the migration files (from this repository)
# - TAHEEL_SPEC.md (this file)
# - IMPLEMENTATION_PLAN.md

# 3. Create virtual environment & install dependencies
python -m venv venv
.\venv\Scripts\activate
pip install openai streamlit python-dotenv PyMuPDF pypdf easyocr fastapi uvicorn pydantic

# 4. Set your API Key in .env
echo "GOOGLE_API_KEY=your_key_here" > .env
```
