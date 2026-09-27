import pytest
from src.taheel.pacing.cognitive_engine import CognitiveLoadBalancer
from src.taheel.schema import OnboardingOntology, RoleProfile, MilestonePhase, SOPItem, ComplexityEnum, LanguageEnum

def test_distribute_sops_to_weeks():
    # Setup mock data
    role = RoleProfile(
        company_name="Test Co",
        department="Ops",
        role_title="Specialist",
        language=LanguageEnum.ENGLISH
    )
    
    # Phase 1 has 3 SOPs of varying complexity
    phase1 = MilestonePhase(
        phase_number=1,
        phase_title="Learn",
        day_range="Days 1-30",
        core_focus="Basics",
        target_sops=[
            SOPItem(sop_id="S1", title="A", summary="A", target_tools=[], complexity=ComplexityEnum.LOW, relevance_to_role="Yes"),
            SOPItem(sop_id="S2", title="B", summary="B", target_tools=[], complexity=ComplexityEnum.HIGH, relevance_to_role="Yes"),
            SOPItem(sop_id="S3", title="C", summary="C", target_tools=[], complexity=ComplexityEnum.CRITICAL, relevance_to_role="Yes"),
        ]
    )
    
    # Phase 2 has 1 SOP
    phase2 = MilestonePhase(
        phase_number=2,
        phase_title="Apply",
        day_range="Days 31-60",
        core_focus="Action",
        target_sops=[
            SOPItem(sop_id="S4", title="D", summary="D", target_tools=[], complexity=ComplexityEnum.MEDIUM, relevance_to_role="Yes")
        ]
    )
    
    ontology = OnboardingOntology(
        role_profile=role,
        identified_tools=[],
        phases=[phase1, phase2],
        raw_sops_count=4
    )
    
    balancer = CognitiveLoadBalancer(ontology)
    schedule = balancer.distribute_sops_to_weeks()
    
    # Week 1 should have S1 (LOW = 1 day) and S2 (HIGH = 3 days). Total = 4 days (fits in 5)
    # Week 2 should have S3 (CRITICAL = 4 days)
    # Phase 1 is weeks 1-4.
    
    assert "S1" in [s.sop_id for s in schedule[1]]
    assert "S2" in [s.sop_id for s in schedule[1]]
    assert "S3" in [s.sop_id for s in schedule[2]]
    
    # Phase 2 starts at week 5. It should have S4 (MEDIUM = 2 days)
    assert "S4" in [s.sop_id for s in schedule[5]]
