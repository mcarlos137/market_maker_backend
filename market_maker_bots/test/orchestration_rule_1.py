import os
import sys
import asyncio
sys.path.append(os.getcwd())
from orchestrationRules.base import OrchestrationRulesBase
from orchestrationRules.strategies.sell_by_range import OrchestrationRulesSellByRange
from damexCommons.base import Trade, TradeSide


orchestration_rules_base = OrchestrationRulesBase(
                orchestration_rule_id='7', 
                exchanges_apis={},
                start_time=23435343453,
                active=True,
                members=["taker_102_ireland", "maker_102_ireland"],
                target_initial_timestamp=None,
                tick_time=2,
                excluded_days=[]
                )
            
orchestration_rules = OrchestrationRulesSellByRange(orchestration_rules_base=orchestration_rules_base)   
#asyncio.run(orchestration_rules.send_balance_alert(channel='telegram_group_1', exchange='bitmart', base_asset='HOT', base_amount=20, quote_asset='USDT', quote_amount=34.544))
#asyncio.run(orchestration_rules.send_status_alert(channel='sdfsdf'))
trades = [
    Trade(bot_id='102', strategy_id='maker_bitmart_holo_v1', base_asset='HOT', quote_asset='USDT', timestamp=1727323873000, order_id='', side=TradeSide.SELL, price=0.9, amount=300, fee={'cost': 12, 'currency': 'USDT'}, exchange_id='erwreteer', exchange='bitmart'),
    Trade(bot_id='102', strategy_id='taker_bitmart_holo_v1', base_asset='HOT', quote_asset='USDT', timestamp=1727323873001, order_id='', side=TradeSide.SELL, price=1, amount=100, fee={'cost': 10, 'currency': 'USDT'}, exchange_id='erwreteer', exchange='bitmart'),
    Trade(bot_id='102', strategy_id='taker_bitmart_holo_v1', base_asset='HOT', quote_asset='USDT', timestamp=1727323873002, order_id='', side=TradeSide.SELL, price=1, amount=200, fee={'cost': 8, 'currency': 'USDT'}, exchange_id='erwreteer', exchange='bitmart')
]
asyncio.run(orchestration_rules.send_trades_sell_report_alert(channel='telegram_group_1', template='strategy', exchange='bitmart', base_asset='HOT', quote_asset='USDT', trades=trades))
#asyncio.run(orchestration_rules.export_all_trades(base_asset='HOT', quote_asset='USDT', trades=trades, member='spreadsheet_main_1', template='resume'))
#orchestration_rules.run() 