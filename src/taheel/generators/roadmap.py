import json
from typing import Dict, Any, List
from src.taheel.schema import MasterRoadmap, OnboardingOntology, RoleProfile
from src.taheel.llm_provider import llm_manager

class RoadmapGenerator:
    """
    Generator that creates the Master 30-60-90 Day Roadmap
    from the structured OnboardingOntology.
    """
    
    SYSTEM_PROMPT = """You are an Executive HR & Operations Director.
Create the Master 30-60-90 Day Onboarding Roadmap for {role_title} at {company_name}.

The roadmap must be structured as a 13-week schedule divided into:
- Phase 1: Days 1 to 30 (Foundation & Orientation)
- Phase 2: Days 31 to 60 (Core Execution & Guided Autonomy)
- Phase 3: Days 61 to 90 (Full Ownership & Final Probation Assessment)

Rules:
- Week 2 must end with the "Day 14 Early Healthcheck Gate".
- Week 4 must end with the "Day 30 Foundation Review".
- Week 8 must end with the "Day 60 Execution Review".
- Week 12 or 13 must end with the "Day 90 Final Probation Decision Gate (Saudi Labor Law Art. 53)".

Return a valid JSON matching the requested structure."""

    def __init__(self):
        pass

    def generate(self, ontology: OnboardingOntology) -> MasterRoadmap:
        """Generates the MasterRoadmap from the ontology."""
        
        schema_json = json.dumps(MasterRoadmap.model_json_schema(), indent=2)
        
        prompt = self.SYSTEM_PROMPT.format(
            role_title=ontology.role_profile.role_title,
            company_name=ontology.role_profile.company_name
        )
        
        prompt += f"\n\nCRITICAL: Your JSON output MUST exactly match this JSON Schema:\n{schema_json}"
        
        # Serialize the ontology to feed to the LLM
        ontology_json = ontology.model_dump_json(indent=2)
        
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"Generate the roadmap based on this ontology:\n\n{ontology_json}"}
        ]
        
        schema = MasterRoadmap.model_json_schema()
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
            
            # Inject the RoleProfile before instantiating to pass Pydantic validation
            data["role_profile"] = ontology.role_profile.model_dump()
            roadmap = MasterRoadmap(**data)
            return roadmap
        except Exception as e:
            raise RuntimeError(f"Failed to generate roadmap: {e}")
