import json
import os
import sys
sys.path.append(os.getcwd())
from maker.base import MakerBotBase
from maker.strategies.default import MakerBotDefault, MakerBotDefaultAscendex, MakerBotDefaultTidex, MakerBotDefaultCoinstore
from maker.strategies.clob import MakerBotCLOB
from maker.strategies.hedge import MakerBotHedge
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
        
    maker_bot_base = MakerBotBase(
        bot_id=bot_id,
        bot_type=bot_type,
        active = active,
        commons=commons,
        exchange=exchange_or_connector,
        quote_asset=quote_asset,
        base_asset=base_asset,
        tick_time=tick_time,
    ) 
                
    match exchange_or_connector:
        case 'tidex':
            if bot_type == 'maker':
                maker_bot = MakerBotDefaultTidex(maker_bot_base=maker_bot_base)
        case 'ascendex':
            if bot_type == 'maker':
                maker_bot = MakerBotDefaultAscendex(maker_bot_base=maker_bot_base)
        case 'coinstore':
            if bot_type == 'maker':
                maker_bot = MakerBotDefaultCoinstore(maker_bot_base=maker_bot_base)
        case 'bitmart' | 'mexc' | 'binance':
            if bot_type == 'maker':
                maker_bot = MakerBotDefault(maker_bot_base=maker_bot_base)
        case 'gateio' | 'bitstamp':
            if bot_type == 'maker':
                maker_bot = MakerBotDefault(maker_bot_base=maker_bot_base)
            if bot_type == 'maker_hedge':
                key = key = 'b2c2' + '__' + base_asset + '-' + quote_asset
                commons[key] = get_commons(base_asset=base_asset, quote_asset=quote_asset, exchange_or_connector='b2c2', api_or_wallet=None)
                if len(commons) < 2:
                    raise RuntimeError('Wrong configuration to start bot')
                maker_bot = MakerBotHedge(
                    maker_bot_base=MakerBotBase(
                        bot_id=bot_id,
                        bot_type=bot_type,
                        active = active,
                        commons=commons,
                        exchange=exchange_or_connector,
                        quote_asset=quote_asset,
                        base_asset=base_asset,
                        tick_time=tick_time,
                    )
                )
        case 'jupiter':
            if bot_type == 'maker_clob':
                maker_bot = MakerBotCLOB(maker_bot_base=maker_bot_base)
            
    maker_bot.run()
