import pytest
import json
from unittest.mock import patch, MagicMock
from src.taheel.generators import OntologyGenerator, RoadmapGenerator, DailyTaskGenerator, ManagerGateGenerator
from src.taheel.schema import RoleProfile, LanguageEnum, SOPItem, ComplexityEnum, MilestonePhase, OnboardingOntology

@pytest.fixture
def mock_role_profile():
    return RoleProfile(
        company_name="Acme Corp",
        department="Engineering",
        role_title="Backend Developer",
        language=LanguageEnum.ENGLISH
    )

@pytest.fixture
def mock_ontology(mock_role_profile):
    phase1 = MilestonePhase(
        phase_number=1,
        phase_title="Learn",
        day_range="Days 1-30",
        core_focus="Basics",
        target_sops=[
            SOPItem(sop_id="S1", title="A", summary="A", target_tools=[], complexity=ComplexityEnum.LOW, relevance_to_role="Yes")
        ]
    )
    return OnboardingOntology(
        role_profile=mock_role_profile,
        identified_tools=["Git"],
        phases=[phase1],
        raw_sops_count=1
    )

@patch('src.taheel.generators.ontology.llm_manager.generate_chat_completion')
def test_ontology_generator(mock_llm, mock_role_profile):
    # Mock LLM response to match OnboardingOntology schema
    mock_response = {
        "role_profile": mock_role_profile.model_dump(),
        "identified_tools": ["Git", "Docker"],
        "phases": [
            {
                "phase_number": 1,
                "phase_title": "Onboarding",
                "day_range": "Days 1-30",
                "core_focus": "Setup",
                "target_sops": [
                    {
                        "sop_id": "S1",
                        "title": "Git Flow",
                        "summary": "How to push code",
                        "target_tools": ["Git"],
                        "complexity": "low",
                        "relevance_to_role": "Needed daily"
                    }
                ]
            }
        ],
        "raw_sops_count": 1
    }
    mock_llm.return_value = json.dumps(mock_response)
    
    gen = OntologyGenerator()
    ontology = gen.generate("Some raw text", mock_role_profile)
    
    assert ontology.raw_sops_count == 1
    assert len(ontology.phases) == 1
    assert ontology.phases[0].target_sops[0].sop_id == "S1"

@patch('src.taheel.generators.roadmap.llm_manager.generate_chat_completion')
def test_roadmap_generator(mock_llm, mock_ontology):
    mock_response = {
        "weeks": [
            {
                "week_number": 1,
                "day_range": "Days 1-5",
                "phase_number": 1,
                "theme": "Setup",
                "core_sops": ["S1"],
                "hands_on_milestone": "Push first commit"
            }
        ]
    }
    mock_llm.return_value = json.dumps(mock_response)
    
    gen = RoadmapGenerator()
    roadmap = gen.generate(mock_ontology)
    
    assert len(roadmap.weeks) == 1
    assert roadmap.weeks[0].theme == "Setup"
    assert roadmap.role_profile.company_name == "Acme Corp"

@patch('src.taheel.generators.daily_tasks.llm_manager.generate_chat_completion')
def test_daily_task_generator(mock_llm, mock_role_profile, mock_ontology):
    mock_response = {
        "day_number": 1,
        "week_number": 1,
        "phase_number": 1,
        "topic": "Git Flow",
        "estimated_minutes": 25,
        "tools_needed": ["Git"],
        "daily_mission": "Learn to commit",
        "sop_principles": ["Rebase"],
        "common_mistakes_to_avoid": ["Force push"],
        "hands_on_action_task": "Push a commit",
        "verification_deliverable": "Commit link",
        "completed": False
    }
    mock_llm.return_value = json.dumps(mock_response)
    
    gen = DailyTaskGenerator()
    sop = mock_ontology.phases[0].target_sops[0]
    task = gen.generate(1, 1, 1, sop, mock_role_profile)
    
    assert task.topic == sop.title
    assert task.estimated_minutes == 25
    assert task.daily_mission == "Learn to commit"

@patch('src.taheel.generators.manager_gates.llm_manager.generate_chat_completion')
def test_manager_gate_generator(mock_llm, mock_role_profile, mock_ontology):
    mock_response = {
        "gate_day": 14,
        "milestone_name": "Healthcheck",
        "target_phase": 1,
        "key_competencies_to_verify": ["Git"],
        "one_on_one_questions": ["How is it going?"],
        "red_flags": ["No commits"],
        "probation_readiness_rubric": {"Technical": "Score 1-5"}
    }
    mock_llm.return_value = json.dumps(mock_response)
    
    gen = ManagerGateGenerator()
    phase = mock_ontology.phases[0]
    gate = gen.generate(14, "Healthcheck", 1, phase, mock_role_profile)
    
    assert gate.gate_day == 14
    assert gate.milestone_name == "Healthcheck"
    assert len(gate.key_competencies_to_verify) == 1
