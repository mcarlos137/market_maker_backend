import json


a = '[{"id": "2", "type": "delay", "value": "PREV__1m", "actions": ["or__compare_balance__binance_HOT_total_lower_20000_rules(3,4)", "or__compare_balance__binance_HOT_total_lower_30000_rules(3,4,10,11,12,13,14,15)"], "member": "or_1_ireland", "apply_on_target_completed": false}]'

print('a', a)

b = json.loads(a)

print('b', b)