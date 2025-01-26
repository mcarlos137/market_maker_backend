import os
import sys
sys.path.append(os.getcwd())
from orchestrationRules.base import OrchestrationRules, OrchestrationRulesBase


class OrchestrationRulesNoTarget(OrchestrationRules):
    
    def __init__(self, orchestration_rules_base: OrchestrationRulesBase) -> None:
        super().__init__(orchestration_rules_base=orchestration_rules_base)
                   
    async def set_target(self, balance: dict, period_in_milliseconds: int) -> None:
        raise NotImplementedError