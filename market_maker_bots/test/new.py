#members = [
#    'maker_101_ireland',
#    'taker_101_ireland'
#]
#members_str = ' '.join([str(elem) for elem in members])
#print('----------------', members_str)

import json
from datetime import datetime
import pytz
from typing import Optional
import time


def refresh_rules(current_time: Optional[int] = None, only_ids: Optional[list] = []):
        with open('rules.json') as f:
            basic_rules = json.load(f)
            start_time = '04:00:00'
            start_time = int(datetime.now(pytz.timezone('UTC')).replace(hour=int(start_time.split(':')[0]), minute=int(start_time.split(':')[1]), second=int(start_time.split(':')[2]), microsecond=0).timestamp() * 1000)
            if current_time is not None:
                start_time = current_time
            print(f'start_time -> {str(datetime.fromtimestamp(start_time / 1e3).time())}')
            previous_time = start_time
            rules = []
            for basic_rule in basic_rules:      
                id = basic_rule['id']
                if len(only_ids) > 0:
                    if id not in only_ids:
                        continue
                delay_from = basic_rule['delay'].split('__')[0]
                delay_period = basic_rule['delay'].split('__')[1]
                if delay_from == 'START':
                    delay_period_time = get_delay_period(period=delay_period)
                    rule_time = start_time + delay_period_time
                elif delay_from == 'PREV':
                    delay_period_time = get_delay_period(period=delay_period)
                    rule_time = previous_time + delay_period_time
                rule = {
                    'id': id,
                    'type': 'time',
                    'value': 'DAY__' + str(rule_time),
                    'actions': basic_rule['actions'],
                    'member': basic_rule['member'],
                    'apply_on_target_completed': basic_rule['apply_on_target_completed'],
                }
                rules.append(rule)
                previous_time = rule_time
            print(f'rules -> {rules}')
        
def get_delay_period(period: str):
    if 's' in period:
        return int(int(period.replace('s', '')) * 1e3)
    elif 'm' in period:
        return int(int(period.replace('m', '')) * 60 * 1e3)
    elif 'h' in period:
        return int(int(period.replace('h', '')) * 60 * 60 * 1e3)
    return 0
    
base_asset = 'HOT'
balance = {
    'HOT': {'total': 10000}
}

actions = [
    #'balance__binance_total_lower_20000_rules(5)', 
    'balance__binance_total_lower_80000_rules(5,11,12,13,14)'
]

for action in actions:
    action_type = action.split('__')[0]
    action_value = action.split('__')[1]

    exchange = str(action_value.split('_')[0])
    type = str(action_value.split('_')[1])
    compare = str(action_value.split('_')[2])
    amount = float(action_value.split('_')[3])
    or_action = str(action_value.split('_')[4])
    execute_or_action = False                                                
    base_balance = float(balance[base_asset][type])
    match compare:
        case 'lower':
            if amount > base_balance:
                execute_or_action = True
        case 'higher':    
            if amount < base_balance:
                execute_or_action = True
    if execute_or_action:
        if 'rules' in or_action:
            new_rules = or_action.replace('rules[', '').replace(']', '').split(',')
            print('new_rules', new_rules)
            refresh_rules(current_time=int(time.time() * 1e3), only_ids=new_rules)
