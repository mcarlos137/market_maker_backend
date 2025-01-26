import logging
import os
import sys
sys.path.append(os.getcwd())
from damexCommons.tools.utils import send_alert
from orchestrationRules.base import OrchestrationRules, OrchestrationRulesBase
from damexCommons.tools.damex_http_client import get_main_price, create_target, create_target_failed

class OrchestrationRulesSellByRange(OrchestrationRules):
    
    def __init__(self, orchestration_rules_base: OrchestrationRulesBase) -> None:
        super().__init__(orchestration_rules_base=orchestration_rules_base)
                   
    async def set_target(self, balance: dict, period_in_milliseconds: int) -> None:
        try:
            target_amount = None
            for target_range in self.target['ranges']:
                price_floor = float(target_range['price_floor'])
                price_ceiling = float(target_range['price_ceiling'])
                amount = float(target_range['amount'])
                current_price = await get_main_price(base_asset=self.target['base_asset'], quote_asset=self.target['quote_asset'], price_decimals=self.commons[self.target['exchange'] + '__' + self.target['base_asset'] + '-' + self.target['quote_asset']].price_decimals)
                if current_price < price_ceiling and current_price >= price_floor:
                    target_amount = amount
                    break
            if target_amount is None or (balance[self.target['base_asset']]['total'] < target_amount):
                await create_target_failed(
                    target_id=self.get_target_id
                )
                send_alert(alert_type='or_target_failed', message_values={
                    'id': self.orchestration_rule_id,
                    'region': 'ireland',
                    'exchange': self.target['exchange'],
                    'base_asset': self.target['base_asset'],
                    'quote_asset': self.target['quote_asset'],
                    'operation': 'SELL',
                }, channel='telegram_group_1')
                return
            await create_target(
                target_id=self.get_target_id,
                initial_timestamp=self.target_initial_timestamp,
                final_timestamp=self.target_initial_timestamp + period_in_milliseconds,
                asset=self.target['base_asset'],
                initial_asset_amount=balance[self.target['base_asset']]['total'],
                operation='SELL',
                operation_amount=target_amount
            )
            print('7')
        except Exception as e:
            logging.error('set target %s', e)
            raise Exception