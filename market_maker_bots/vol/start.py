import json
import os
import sys
sys.path.append(os.getcwd())
from vol.base import VolBotBase
from vol.strategies.clob import VolBotCLOB
from vol.strategies.liquidity_pool import VolBotLiquidityPool
from vol.strategies.default import VolBotDefault, VolBotDefaultAscendex, VolBotDefaultTidex, VolBotDefaultCoinstore
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
            
    vol_bot_base = VolBotBase(
        bot_id=bot_id,
        bot_type=bot_type,
        active=active,
        commons=commons,
        exchange=exchange_or_connector,
        base_asset=base_asset,
        quote_asset=quote_asset,
        tick_time=tick_time,
    ) 
    
    match(exchange_or_connector):
        case 'tidex':
            if bot_type == 'vol':
                vol_bot = VolBotDefaultTidex(vol_bot_base=vol_bot_base)
        case 'ascendex':
            if bot_type == 'vol':
                key = key = exchange_or_connector + '_aux' + '__' + base_asset + '-' + quote_asset
                commons[key] = get_commons(base_asset=base_asset, quote_asset=quote_asset, exchange_or_connector=exchange_or_connector, api_or_wallet='ascendex__vol_aux')
                if len(commons) < 2:
                    raise RuntimeError('Wrong configuration to start bot')
                vol_bot_base = VolBotBase(
                    bot_id=bot_id,
                    bot_type=bot_type,
                    active=active,
                    commons=commons,
                    exchange=exchange_or_connector,
                    base_asset=base_asset,
                    quote_asset=quote_asset,
                    tick_time=tick_time,
                )
                vol_bot = VolBotDefaultAscendex(vol_bot_base=vol_bot_base)
        case 'coinstore':
            if bot_type == 'vol':
                vol_bot = VolBotDefaultCoinstore(vol_bot_base=vol_bot_base)
        case 'mexc' | 'bitmart' | 'gateio' | 'bitstamp':
            if bot_type == 'vol':
                vol_bot = VolBotDefault(vol_bot_base=vol_bot_base)
        case 'uniswap' | 'raydium':
            if bot_type == 'vol_lp':
                vol_bot = VolBotLiquidityPool(vol_bot_base=vol_bot_base)
        case 'jupiter':
            if bot_type == 'vol_clob':
                vol_bot = VolBotCLOB(vol_bot_base=vol_bot_base)
            
    vol_bot.run()
