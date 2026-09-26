import os
import zipfile
import io
from typing import List
from pathlib import Path
from src.taheel.schema import (
    OnboardingPackage, 
    MasterRoadmap, 
    DailyMicroTask, 
    ManagerEvaluationGate
)

class NotionExporter:
    """
    Exports Taheel AI onboarding packages into Notion-ready Markdown 
    files and `.zip` archives.
    """
    
    @staticmethod
    def render_roadmap(roadmap: MasterRoadmap) -> str:
        """Renders the Master Roadmap into a clean Markdown table."""
        prof = roadmap.role_profile
        md = [
            f"# 🗺️ Master 30-60-90 Day Roadmap",
            f"**Role:** {prof.role_title} | **Department:** {prof.department} | **Company:** {prof.company_name}\n",
        ]
        
        # Group weeks by phase
        phases = {1: [], 2: [], 3: []}
        for week in roadmap.weeks:
            if week.phase_number in phases:
                phases[week.phase_number].append(week)
                
        phase_titles = {
            1: "Phase 1: Foundation & Orientation (Days 1-30)",
            2: "Phase 2: Core Execution & Guided Autonomy (Days 31-60)",
            3: "Phase 3: Full Ownership & Probation Assessment (Days 61-90)"
        }
        
        for p_num in range(1, 4):
            if not phases[p_num]:
                continue
            md.append(f"## 📍 {phase_titles[p_num]}")
            md.append("| Week | Day Range | Core SOPs / Topics | Hands-On Milestone Task | Manager Gate / Checkpoint |")
            md.append("|------|-----------|--------------------|-------------------------|---------------------------|")
            for w in phases[p_num]:
                sops = "<br>".join(w.core_sops) if w.core_sops else "None"
                chk = w.manager_checkpoint if w.manager_checkpoint else "—"
                md.append(f"| Week {w.week_number} | {w.day_range} | {sops} | {w.hands_on_milestone} | {chk} |")
            md.append("\n")
            
        return "\n".join(md)

    @staticmethod
    def render_daily_task(task: DailyMicroTask) -> str:
        """Renders a single Daily Micro-Task card into Notion-ready Markdown."""
        md = [
            f"# ☀️ Day {task.day_number}: {task.topic}",
            f"> ⏱️ **Estimated Time:** {task.estimated_minutes} minutes",
            f"> 🏢 **Tools Needed:** {', '.join(task.tools_needed) if task.tools_needed else 'None'}\n",
            
            f"## 🎯 1. Daily Mission",
            f"{task.daily_mission}\n",
            
            f"## 📜 2. Core SOP Rules & Standards"
        ]
        
        for rule in task.sop_principles:
            md.append(f"- {rule}")
        md.append("")
        
        if task.common_mistakes_to_avoid:
            # Using Notion callout block style or Github alert
            md.append(f"> [!WARNING]")
            md.append(f"> **Common Mistakes to Avoid:**")
            for mistake in task.common_mistakes_to_avoid:
                md.append(f"> - {mistake}")
            md.append("")
            
        md.append(f"## 🛠️ 3. Hands-On Workplace Task")
        md.append(f"{task.hands_on_action_task}\n")
        
        md.append(f"## ✅ 4. Progress Checkbox")
        md.append(f"- [ ] Task executed and verified")
        md.append(f"- [ ] {task.verification_deliverable}")
        
        return "\n".join(md)

    @staticmethod
    def render_manager_gate(gate: ManagerEvaluationGate, prof) -> str:
        """Renders a Manager Evaluation Gate into a formal Markdown rubric."""
        md = [
            f"# 🛡️ Manager Milestone Evaluation: Day {gate.gate_day}",
            f"**Milestone:** {gate.milestone_name}",
            f"**Employee:** {prof.employee_name} | **Manager:** {prof.mentor_name} | **Date:** _________\n",
            
            f"## ✅ 1. Verification Checklist"
        ]
        
        for comp in gate.key_competencies_to_verify:
            md.append(f"- [ ] {comp}")
        md.append("")
        
        md.append(f"## 💬 2. Guided 1-on-1 Interview Questions")
        for i, q in enumerate(gate.one_on_one_questions, 1):
            md.append(f"{i}. {q}")
        md.append("")
        
        if gate.red_flags:
            md.append(f"## 🚩 3. Red Flags to Watch For")
            for flag in gate.red_flags:
                md.append(f"- 🚩 {flag}")
            md.append("")
            
        if gate.probation_readiness_rubric:
            md.append(f"## 📊 4. Probation Readiness Rubric")
            for k, v in gate.probation_readiness_rubric.items():
                md.append(f"**{k}**: {v}")
            md.append("")
            
        md.append(f"## ⚖️ 5. Saudi Labor Law Article 53 Probation Verdict")
        md.append(f"- [ ] **Exceeds Expectations** — Fast-track to advanced projects")
        md.append(f"- [ ] **On Track** — Proceed to next milestone")
        md.append(f"- [ ] **Action Plan Needed** — Specific 14-day remediation")
        md.append(f"- [ ] **Probation Risk / Do Not Confirm** — Formal HR escalation")
        
        return "\n".join(md)

    @classmethod
    def generate_zip_bundle(cls, package: OnboardingPackage) -> io.BytesIO:
        """
        Generates an in-memory ZIP archive containing the full onboarding package.
        Returns a BytesIO object ready for FastAPI streaming or local writing.
        """
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            # 1. Write Roadmap
            roadmap_md = cls.render_roadmap(package.roadmap)
            zip_file.writestr("00_Master_Roadmap.md", roadmap_md)
            
            # 2. Write Daily Tasks
            for task in package.daily_tasks:
                task_md = cls.render_daily_task(task)
                week_dir = f"01_Daily_Tasks/Week_{task.week_number:02d}"
                filename = f"{week_dir}/Day_{task.day_number:02d}_{task.topic.replace(' ', '_').lower()[:20]}.md"
                zip_file.writestr(filename, task_md)
                
            # 3. Write Manager Gates
            for gate in package.manager_gates:
                gate_md = cls.render_manager_gate(gate, package.role_profile)
                filename = f"02_Manager_Gates/Day_{gate.gate_day:02d}_Review.md"
                zip_file.writestr(filename, gate_md)
                
        zip_buffer.seek(0)
        return zip_buffer

    @classmethod
    def write_bundle_to_disk(cls, package: OnboardingPackage, output_dir: str) -> str:
        """
        Writes the ZIP bundle to disk. Returns the path to the written zip file.
        """
        os.makedirs(output_dir, exist_ok=True)
        safe_role = package.role_profile.role_title.replace(" ", "_").lower()
        zip_path = os.path.join(output_dir, f"{safe_role}_onboarding_bundle.zip")
        
        zip_buffer = cls.generate_zip_bundle(package)
        with open(zip_path, "wb") as f:
            f.write(zip_buffer.getvalue())
            
        return zip_path
