import json
import os
import sys
from pathlib import Path
sys.path.append(os.getcwd())
from arbitrage.base import ArbitrageBotBase
from arbitrage.strategies.default import ArbitrageBotDefault
from arbitrage.strategies.triple import ArbitrageBotTriple
from damexCommons.tools.connections import get_commons

commons = {}

with open('config.json', encoding='UTF-8') as f:
    config = json.load(f)
    bot_id = config['bot_id']
    bot_type = config['bot_type']
    active = config['active']
    exchanges_apis = config['exchanges_apis']
    base_assets = config['base_assets']
    quote_asset = config['quote_asset']
    testing = config['testing']
    emulated_balance = config['emulated_balance']
    strategy_id = config['strategy']
    
    exchanges: list[str] = [] 
    
    pivot_asset = None
        
    if bot_type == 'arbitrage_triple':
        pivot_asset = json.loads(open(str(Path(os.getcwd()).parent.parent) + "/strategy_files/" + strategy_id + ".json", 'r', encoding='UTF-8').read())['pivot_asset']
          
    for exchange in exchanges_apis:
        exchanges.append(exchange)
        for base_asset in base_assets:
            key = exchange + '__' + base_asset + '-' + quote_asset
            commons[key] = get_commons(base_asset=base_asset, quote_asset=quote_asset, exchange_or_connector=exchange, api_or_wallet=exchanges_apis[exchange])
            if pivot_asset is not None:
                key_2 = exchange + '__' + base_asset + '-' + pivot_asset
                commons[key_2] = get_commons(base_asset=base_asset, quote_asset=pivot_asset, exchange_or_connector=exchange, api_or_wallet=exchanges_apis[exchange])
                key_3 = exchange + '__' + pivot_asset + '-' + quote_asset
                commons[key_3] = get_commons(base_asset=pivot_asset, quote_asset=quote_asset, exchange_or_connector=exchange, api_or_wallet=exchanges_apis[exchange])
                                
    if len(commons) < 2 and bot_type == 'arbitrage':
        raise RuntimeError('Wrong configuration to start bot')
    
    if len(commons) < 1 and bot_type == 'arbitrage_triple':
        raise RuntimeError('Wrong configuration to start bot')
                    
    arbitrage_bot_base = ArbitrageBotBase(
        bot_id=bot_id,
        bot_type=bot_type,
        active = active,
        commons=commons,
        exchanges=exchanges,
        base_assets=base_assets,
        quote_asset=quote_asset,
        testing=testing,
        emulated_balance=emulated_balance
    ) 
          
    if bot_type == 'arbitrage':
        arbitrage_bot = ArbitrageBotDefault(arbitrage_bot_base=arbitrage_bot_base)                            
        arbitrage_bot.run()
    elif bot_type == 'arbitrage_triple':
        arbitrage_bot = ArbitrageBotTriple(arbitrage_bot_base=arbitrage_bot_base)                            
        arbitrage_bot.run()