import os
import sys
import asyncio


rules = [
{'id': '1', 'type': 'time', 'value': 'DAY__1728046800000', 'actions': ['or__create_target'], 'member': 'or_1_ireland', 'apply_on_target_completed': False}, 
{'id': '2', 'type': 'time', 'value': 'DAY__1728046860000', 'actions': ['or__compare_balance__bitmart_HOT_total_lower_4000000_rules[3,4]', 'or__compare_balance__bitmart_HOT_total_lower_5000000_rules[3,4,10,11,12,13,14,15]'], 'member': 'or_1_ireland', 'apply_on_target_completed': False}, 
{'id': '3', 'type': 'time', 'value': 'DAY__1728046890000', 'actions': ['alert__send_balance__bitmart_HOT_USDT'], 'member': 'telegram_group_1', 'apply_on_target_completed': False}, 
{'id': '4', 'type': 'time', 'value': 'DAY__1728046920000', 'actions': ['alert__send_status'], 'member': 'telegram_group_1', 'apply_on_target_completed': False}, 
#{'id': '5', 'type': 'time', 'value': 'DAY__1728046980000', 'actions': ['bot__add_target', 'bot__change_strategy__maker_bitmart_holo_v1', 'bot__change_status__restart'], 'member': 'maker_102_ireland', 'apply_on_target_completed': False}, 
#{'id': '6', 'type': 'time', 'value': 'DAY__1728047280000', 'actions': ['bot__change_strategy__maker_bitmart_holo_v2', 'bot__change_status__restart'], 'member': 'maker_102_ireland', 'apply_on_target_completed': False}, 
#{'id': '7', 'type': 'time', 'value': 'DAY__1728047580000', 'actions': ['bot__change_strategy__maker_bitmart_holo_v3', 'bot__change_status__restart'], 'member': 'maker_102_ireland', 'apply_on_target_completed': False}, 
#{'id': '8', 'type': 'time', 'value': 'DAY__1728047880000', 'actions': ['bot__change_strategy__maker_bitmart_holo_v4', 'bot__change_status__restart'], 'member': 'maker_102_ireland', 'apply_on_target_completed': False}, 
#{'id': '9', 'type': 'time', 'value': 'DAY__1728048180000', 'actions': ['bot__change_status__inactivate'], 'member': 'maker_102_ireland', 'apply_on_target_completed': False}, 
#{'id': '10', 'type': 'time', 'value': 'DAY__1728048240000', 'actions': ['bot__add_target', 'bot__change_strategy__taker_bitmart_holo_v1', 'bot__change_status__restart'], 'member': 'taker_102_ireland', 'apply_on_target_completed': False}, 
{'id': '11', 'type': 'time', 'value': 'DAY__1728048540000', 'actions': ['bot__change_status__inactivate'], 'member': 'taker_102_ireland', 'apply_on_target_completed': False}, 
{'id': '12', 'type': 'time', 'value': 'DAY__1728048600000', 'actions': ['alert__send_trades_sell_report__default_bitmart_HOT_USDT', 'alert__send_trades_sell_report__strategy_bitmart_HOT_USDT', 'alert__send_balance__bitmart_HOT_USDT', 'alert__send_status'], 'member': 'telegram_group_1', 'apply_on_target_completed': True}, 
{'id': '13', 'type': 'time', 'value': 'DAY__1728048600000', 'actions': ['alert__send_trades_sell_report__client1_bitmart_HOT_USDT'], 'member': 'telegram_group_2', 'apply_on_target_completed': True}, 
{'id': '14', 'type': 'time', 'value': 'DAY__1728048620000', 'actions': ['data__export_all_trades__details_bitmart_HOT_USDT', 'data__export_all_trades__resume_bitmart_HOT_USDT'], 'member': 'spreadsheet_main_1', 'apply_on_target_completed': True}, 
{'id': '15', 'type': 'time', 'value': 'DAY__1728048620000', 'actions': ['data__export_all_trades__resume_bitmart_HOT_USDT'], 'member': 'spreadsheet_main_2', 'apply_on_target_completed': True}
]


async def get_bot_rules() -> list:
    bot_rules = []
    for rule in rules:
        for actions in rule['actions']:
            if ('bot__change_status__restart' or 'bot__change_status__activate') in actions:
                bot_rules.append(rule)
                break
    return bot_rules

print(len(asyncio.run(get_bot_rules())))