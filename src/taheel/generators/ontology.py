import json
from typing import Dict, Any, List
from src.taheel.schema import OnboardingOntology, RoleProfile, MilestonePhase
from src.taheel.llm_provider import llm_manager

class OntologyGenerator:
    """
    Generator that analyzes raw handbook/SOP text against a RoleProfile 
    and outputs a structured OnboardingOntology.
    """
    
    SYSTEM_PROMPT = """You are an expert Enterprise Workforce Enablement Architect.
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

Return ONLY a valid JSON matching the exact structure requested."""

    def __init__(self):
        pass

    def generate(self, raw_text: str, role_profile: RoleProfile) -> OnboardingOntology:
        """Generates the OnboardingOntology from raw text."""
        
        prompt = self.SYSTEM_PROMPT.format(
            role_title=role_profile.role_title,
            department=role_profile.department,
            company_name=role_profile.company_name,
            language=role_profile.language.value
        )
        
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"Extract the onboarding ontology from the following manual text:\n\n{raw_text[:30000]}"} # Truncate to avoid massive tokens
        ]
        
        # We enforce the JSON schema via structured outputs where possible.
        # Since pydantic provides model_json_schema(), we can pass that.
        schema = OnboardingOntology.model_json_schema()
        
        response_format = {
            "type": "json_schema",
            "json_schema": {
                "name": "OnboardingOntology",
                "schema": schema,
                "strict": True
            }
        }
        
        try:
            raw_response = llm_manager.generate_chat_completion(
                messages=messages,
                temperature=0.1,
                response_format=response_format
            )
            data = json.loads(raw_response)
            return OnboardingOntology(**data)
        except Exception as e:
            raise RuntimeError(f"Failed to generate ontology: {e}")
