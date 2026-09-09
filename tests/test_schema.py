"""
Unit tests for Taheel AI Pydantic Schemas (src/taheel/schema.py).
"""

import pytest
from src.taheel.schema import (
    LanguageEnum,
    ComplexityEnum,
    ProbationVerdictEnum,
    RoleProfile,
    SOPItem,
    MilestonePhase,
    DailyMicroTask,
    ManagerEvaluationGate,
    OnboardingOntology,
    RoadmapWeek,
    MasterRoadmap,
    OnboardingPackage,
)


def test_role_profile():
    profile = RoleProfile(
        company_name="RiyadhPay Fintech",
        department="Customer Operations",
        role_title="Tier-1 Operations Specialist",
        mentor_name="Tariq Al-Mansoor",
        employee_name="Saad Al-Otaibi",
        language=LanguageEnum.ARABIC,
    )
    assert profile.company_name == "RiyadhPay Fintech"
    assert profile.language == LanguageEnum.ARABIC
    assert profile.mentor_name == "Tariq Al-Mansoor"


def test_sop_item():
    sop = SOPItem(
        sop_id="SOP-OPS-001",
        title="Nafath Identity Verification",
        summary="Verifying user biometric identities through Nafath portal",
        target_tools=["RP-Admin", "Nafath Portal", "Zendesk"],
        complexity=ComplexityEnum.MEDIUM,
        relevance_to_role="Essential for onboarding new customers and unblocking KYC",
    )
    assert sop.sop_id == "SOP-OPS-001"
    assert sop.complexity == ComplexityEnum.MEDIUM
    assert len(sop.target_tools) == 3


def test_milestone_phase():
    phase = MilestonePhase(
        phase_number=1,
        phase_title="Foundation & System Orientation",
        day_range="Days 1-30",
        core_focus="Master core tools and security protocols",
        target_sops=[
            SOPItem(
                sop_id="SOP-OPS-001",
                title="KYC Verification",
                summary="Nafath verification",
                relevance_to_role="Tier-1 frontline triage",
            )
        ],
    )
    assert phase.phase_number == 1
    assert len(phase.target_sops) == 1


def test_daily_micro_task():
    task = DailyMicroTask(
        day_number=1,
        week_number=1,
        phase_number=1,
        topic="Introduction to RP-Admin & Account Lookup",
        estimated_minutes=25,
        tools_needed=["RP-Admin Portal"],
        daily_mission="Learn how to securely locate user profiles using National ID.",
        sop_principles=["Always verify 2FA before entering RP-Admin."],
        common_mistakes_to_avoid=["Never search user by unverified nicknames."],
        hands_on_action_task="Perform search simulation in sandbox environment.",
        verification_deliverable="Screenshot of mock search uploaded to ticket.",
    )
    assert task.day_number == 1
    assert task.estimated_minutes == 25
    assert not task.completed


def test_daily_micro_task_validation():
    # Test that time cap constraint (ge=15, le=45) is enforced
    with pytest.raises(ValueError):
        DailyMicroTask(
            day_number=1,
            week_number=1,
            phase_number=1,
            topic="Invalid Time Task",
            estimated_minutes=10,  # Below 15 min limit
            daily_mission="Test mission",
            hands_on_action_task="Test action",
        )

    with pytest.raises(ValueError):
        DailyMicroTask(
            day_number=1,
            week_number=1,
            phase_number=1,
            topic="Invalid Time Task",
            estimated_minutes=60,  # Above 45 min limit (cognitive overload)
            daily_mission="Test mission",
            hands_on_action_task="Test action",
        )


def test_manager_evaluation_gate():
    gate = ManagerEvaluationGate(
        gate_day=14,
        milestone_name="Day 14 Early Healthcheck & Tooling Gate",
        target_phase=1,
        key_competencies_to_verify=[
            "Independent navigation of RP-Admin",
            "Nafath KYC error code comprehension",
        ],
        one_on_one_questions=[
            "How do you handle a customer whose biometric status in Nafath is expired?",
        ],
        red_flags=[
            "Attempting to manually override KYC blocks without authorization",
        ],
        probation_readiness_rubric={
            "tool_proficiency": {"score": 4, "max": 5},
            "compliance_adherence": {"score": 5, "max": 5},
        },
        recommended_verdict=ProbationVerdictEnum.ON_TRACK,
    )
    assert gate.gate_day == 14
    assert gate.recommended_verdict == ProbationVerdictEnum.ON_TRACK


def test_onboarding_package_serialization():
    profile = RoleProfile(
        company_name="RiyadhPay Fintech",
        department="Customer Operations",
        role_title="Tier-1 Operations Specialist",
    )
    ontology = OnboardingOntology(role_profile=profile)
    roadmap = MasterRoadmap(role_profile=profile)

    package = OnboardingPackage(
        package_id="test-pkg-001",
        created_at="2026-09-09T12:00:00Z",
        role_profile=profile,
        ontology=ontology,
        roadmap=roadmap,
        daily_tasks=[],
        manager_gates=[],
    )
    data = package.model_dump()
    assert data["package_id"] == "test-pkg-001"
    assert data["role_profile"]["company_name"] == "RiyadhPay Fintech"
