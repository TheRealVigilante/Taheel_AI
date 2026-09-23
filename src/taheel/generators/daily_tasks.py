import json
from typing import Dict, Any, List
from src.taheel.schema import DailyMicroTask, SOPItem, RoleProfile
from src.taheel.llm_provider import llm_manager

class DailyTaskGenerator:
    """
    Generator that creates practical Daily Micro-Action Cards.
    """
    
    SYSTEM_PROMPT = """You are a Senior Operational Mentor.
Generate a structured Daily Micro-Action Onboarding Card for:
Day #: {day_number} | Week #: {week_number} | Phase #: {phase_number} | Role: {role_title}
Topic / SOP: {topic}

Return ONLY a valid JSON matching the DailyMicroTask structure. 
Rules:
1. Keep the daily_mission focused on real business impact (1-2 sentences).
2. The hands_on_action_task MUST be a concrete simulation or action in the company's real software/tools.
3. Keep estimated_minutes between 15 and 45.
"""

    def __init__(self):
        pass

    def generate(self, day_number: int, week_number: int, phase_number: int, sop: SOPItem, role_profile: RoleProfile) -> DailyMicroTask:
        """Generates a DailyMicroTask for a given SOP."""
        
        prompt = self.SYSTEM_PROMPT.format(
            day_number=day_number,
            week_number=week_number,
            phase_number=phase_number,
            role_title=role_profile.role_title,
            topic=sop.title
        )
        
        sop_json = sop.model_dump_json(indent=2)
        
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"Create the daily task based on this SOP competency:\n\n{sop_json}"}
        ]
        
        schema = DailyMicroTask.model_json_schema()
        response_format = {
            "type": "json_schema",
            "json_schema": {
                "name": "DailyMicroTask",
                "schema": schema,
                "strict": True
            }
        }
        
        try:
            raw_response = llm_manager.generate_chat_completion(
                messages=messages,
                temperature=0.2,
                response_format=response_format
            )
            data = json.loads(raw_response)
            
            # Ensure day/week/phase/topic match exactly what was requested
            data["day_number"] = day_number
            data["week_number"] = week_number
            data["phase_number"] = phase_number
            data["topic"] = sop.title
            
            return DailyMicroTask(**data)
        except Exception as e:
            raise RuntimeError(f"Failed to generate daily task: {e}")
