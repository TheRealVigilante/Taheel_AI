from typing import List, Dict, Any
import math
from src.taheel.schema import OnboardingOntology, SOPItem, ComplexityEnum, MilestonePhase

class CognitiveLoadBalancer:
    """
    Engine to balance learning density across the 90-day probation timeline.
    Ensures that SOPs are paced to prevent cognitive overload (20-30 mins/day limit).
    """

    def __init__(self, ontology: OnboardingOntology):
        self.ontology = ontology
        self.weeks_total = 13  # 90 days / 7 ≈ 13 weeks
        
    def _estimate_sop_duration_days(self, sop: SOPItem) -> int:
        """Estimates how many days an SOP will take to learn based on complexity."""
        if sop.complexity == ComplexityEnum.LOW:
            return 1
        elif sop.complexity == ComplexityEnum.MEDIUM:
            return 2
        elif sop.complexity == ComplexityEnum.HIGH:
            return 3
        else: # CRITICAL
            return 4

    def distribute_sops_to_weeks(self) -> Dict[int, List[SOPItem]]:
        """
        Distributes SOPs into the 13-week schedule.
        Returns a dictionary mapping week_number (1-13) to a list of SOPItems.
        """
        weekly_schedule: Dict[int, List[SOPItem]] = {week: [] for week in range(1, 14)}
        
        # Max days of training per week (assuming 5 working days)
        # Cap is around 5 tasks/week. We'll track capacity.
        week_capacity = {week: 5 for week in range(1, 14)}
        
        # We process phase by phase.
        for phase in self.ontology.phases:
            # Phase 1: Weeks 1-4 (Days 1-30 approx)
            # Phase 2: Weeks 5-8 (Days 31-60 approx)
            # Phase 3: Weeks 9-13 (Days 61-90 approx)
            
            if phase.phase_number == 1:
                available_weeks = list(range(1, 5))
            elif phase.phase_number == 2:
                available_weeks = list(range(5, 9))
            else:
                available_weeks = list(range(9, 14))
                
            # Sort SOPs within phase by complexity (simplest first)
            complexity_order = {
                ComplexityEnum.LOW: 0,
                ComplexityEnum.MEDIUM: 1,
                ComplexityEnum.HIGH: 2,
                ComplexityEnum.CRITICAL: 3
            }
            sorted_sops = sorted(phase.target_sops, key=lambda s: complexity_order.get(s.complexity, 1))
            
            # Place SOPs in available weeks
            current_week_idx = 0
            for sop in sorted_sops:
                days_needed = self._estimate_sop_duration_days(sop)
                
                placed = False
                while current_week_idx < len(available_weeks) and not placed:
                    week = available_weeks[current_week_idx]
                    
                    if week_capacity[week] >= days_needed:
                        weekly_schedule[week].append(sop)
                        week_capacity[week] -= days_needed
                        placed = True
                    else:
                        # Move to next week
                        current_week_idx += 1
                        
                # If we couldn't place it within the phase's weeks due to overload, 
                # just put it in the last available week of the phase and let it overflow.
                if not placed:
                    last_week = available_weeks[-1]
                    weekly_schedule[last_week].append(sop)
                    week_capacity[last_week] -= days_needed
                    
        return weekly_schedule
