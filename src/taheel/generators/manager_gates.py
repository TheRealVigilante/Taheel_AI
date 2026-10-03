import json
from typing import Dict, Any, List
from src.taheel.schema import ManagerEvaluationGate, RoleProfile, MilestonePhase
from src.taheel.llm_provider import llm_manager

class ManagerGateGenerator:
    """
    Generator that creates formal 1-on-1 Milestone Evaluation Gates 
    conducted by the line manager at Days 14, 30, 60, and 90.
    """
    
    SYSTEM_PROMPT = """You are a Chief People Officer and Legal Compliance Specialist.
Generate the formal Manager 1-on-1 Evaluation Rubric for:
Milestone: Day {gate_day} ({milestone_name})
Role: {role_title} | Department: {department} | Company: {company_name}

Rules:
1. Align with Saudi Labor Law Article 53 Probation requirements.
2. The key_competencies_to_verify MUST be concrete skills the employee must demonstrate live.
3. one_on_one_questions MUST include probing and scenario-based interview questions.
4. probation_readiness_rubric MUST be a dictionary mapping string keys (like 'Technical Proficiency', 'Culture Fit') to an explanation of what a score of 1-5 means.

Return ONLY a valid JSON matching the ManagerEvaluationGate structure."""

    def __init__(self):
        pass

    def generate(self, gate_day: int, milestone_name: str, target_phase: int, phase_data: MilestonePhase, role_profile: RoleProfile) -> ManagerEvaluationGate:
        """Generates a ManagerEvaluationGate for a specific milestone day."""
        
        schema_json = json.dumps(ManagerEvaluationGate.model_json_schema(), indent=2)
        
        prompt = self.SYSTEM_PROMPT.format(
            gate_day=gate_day,
            milestone_name=milestone_name,
            role_title=role_profile.role_title,
            department=role_profile.department,
            company_name=role_profile.company_name
        )
        
        prompt += f"\n\nCRITICAL: Your JSON output MUST exactly match this JSON Schema:\n{schema_json}"
        
        phase_json = phase_data.model_dump_json(indent=2)
        
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"Create the evaluation gate based on the focus and SOPs of this phase:\n\n{phase_json}"}
        ]
        
        schema = ManagerEvaluationGate.model_json_schema()
        response_format = {
            "type": "json_object"
        }
        
        try:
            raw_response = llm_manager.generate_chat_completion(
                messages=messages,
                temperature=0.2,
                response_format=response_format
            )
            data = json.loads(raw_response)
            
            # Ensure static fields match
            data["gate_day"] = gate_day
            data["milestone_name"] = milestone_name
            data["target_phase"] = target_phase
            
            return ManagerEvaluationGate(**data)
        except Exception as e:
            raise RuntimeError(f"Failed to generate manager gate: {e}")
