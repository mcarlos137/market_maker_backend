import json
import os
import sys
sys.path.append(os.getcwd())
from taker.base import TakerBotBase
from taker.strategies.default import TakerBotDefault, TakerBotDefaultAscendex, TakerBotDefaultTidex
from taker.strategies.clob import TakerBotCLOB
from damexCommons.tools.connections import get_commons

commons = {}
exchange_or_connector = None

with open('config.json', encoding='UTF-8') as f:
    config = json.load(f)
    bot_id = config['bot_id']
    bot_type = config['bot_type']
    active = config['active']
    base_asset = config['base_asset']
    quote_asset = config['quote_asset']
    tick_time = config['tick_time']
    
    exchanges_or_connectors_fields = ['exchange', 'connector']
    
    for exchange_or_connector_field in exchanges_or_connectors_fields:
        api_or_wallet = None
        if exchange_or_connector_field in config:
            if 'api' in config:
                api_or_wallet = config['api']
            elif 'wallet' in config:
                api_or_wallet = config['wallet']
            exchange_or_connector = config[exchange_or_connector_field]
        if api_or_wallet is None:
            continue
        key = exchange_or_connector + '__' + base_asset + '-' + quote_asset
        commons[key] = get_commons(base_asset=base_asset, quote_asset=quote_asset, exchange_or_connector=exchange_or_connector, api_or_wallet=api_or_wallet)
    
    if len(commons) < 1:
        raise RuntimeError('Wrong configuration to start bot')
        
    taker_bot_base = TakerBotBase(
        bot_id=bot_id,
        bot_type=bot_type,
        active = active,
        commons=commons,
        exchange=exchange_or_connector,
        base_asset=base_asset,
        quote_asset=quote_asset,   
        tick_time=tick_time,       
    ) 
        
    match(exchange_or_connector):
        case 'ascendex':
            if bot_type == 'taker':
                taker_bot = TakerBotDefaultAscendex(taker_bot_base=taker_bot_base)
        case 'tidex':
            if bot_type == 'taker':
                taker_bot = TakerBotDefaultTidex(taker_bot_base=taker_bot_base)
        case 'mexc' | 'bitmart' | 'coinstore' | 'binance' | 'gateio' | 'bitstamp':
            if bot_type == 'taker':
                taker_bot = TakerBotDefault(taker_bot_base=taker_bot_base)
        case 'jupiter':
            if bot_type == 'taker_clob':
                taker_bot = TakerBotCLOB(taker_bot_base=taker_bot_base)
            
    taker_bot.run()
