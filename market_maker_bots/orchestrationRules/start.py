import json
import os
import sys
sys.path.append(os.getcwd())
from orchestrationRules.base import OrchestrationRulesBase
from orchestrationRules.strategies.sell_by_range import OrchestrationRulesSellByRange
from orchestrationRules.strategies.no_target import OrchestrationRulesNoTarget

    
with open('config.json', encoding='UTF-8') as f:
    config = json.load(f)
    orchestration_rule_id = config['orchestration_rule_id']
    exchanges_apis = config['exchanges_apis']
    strategy = config['strategy']
    start_time = config['start_time']
    active = config['active']
    members = config['members']
    target_initial_timestamp = config['target_initial_timestamp']
    tick_time = config['tick_time']  
    excluded_days = config['excluded_days']
                    
    orchestration_rules_base = OrchestrationRulesBase(
                orchestration_rule_id=orchestration_rule_id, 
                exchanges_apis=exchanges_apis,
                start_time=start_time,
                active=active,
                members=members,
                target_initial_timestamp=target_initial_timestamp,
                tick_time=tick_time,
                excluded_days=excluded_days
                )
            
    match strategy:
        case 'sell_by_range':
            orchestration_rules = OrchestrationRulesSellByRange(
                orchestration_rules_base=orchestration_rules_base
            )    
        case 'no_target': 
            orchestration_rules = OrchestrationRulesNoTarget(
                orchestration_rules_base=orchestration_rules_base
            )     

    orchestration_rules.run()
