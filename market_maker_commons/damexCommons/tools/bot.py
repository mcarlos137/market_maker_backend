import json
import os

STRATEGY_PARAMS = {
    'maker': [
        {'name': 'max_order_age', 'type': 'int'},
        {'name': 'order_refresh_time_uptrend', 'type': 'int'},
        {'name': 'order_price_refresh_tolerance_pct_uptrend', 'type': 'float'},
        {'name': 'order_refresh_time_downtrend', 'type': 'int'},
        {'name': 'order_price_refresh_tolerance_pct_downtrend', 'type': 'float'},
        {'name': 'order_price_refresh_tolerance_pct', 'type': 'float'},
        {'name': 'price_api_update_interval', 'type': 'int'},
        {'name': 'add_transaction_costs', 'type': 'bool'},
        {'name': 'spread', 'type': 'json', 'format': '{"ASK": "float", "BID": "float"}'},
        {'name': 'order_amount', 'type': 'json', 'format': '{"ASK": "float", "BID": "float"}'},
        {'name': 'order_levels', 'type': 'json', 'format': '{"ASK": "int", "BID": "int"}'},
        {'name': 'order_level_amount', 'type': 'json', 'format': '{"ASK": "float", "BID": "float"}'},
        {'name': 'order_level_spread', 'type': 'json', 'format': '{"ASK": "float", "BID": "float"}'},
        {'name': 'order_refresh_level_min', 'type': 'json', 'format': '{"ASK": "int", "BID": "int"}'},
        {'name': 'trade_amount_limit_1h', 'type': 'json', 'format': '{"SELL": "int", "BUY": "int"}'},
        ],
    'maker_clob': [
        {'name': 'order_refresh_time', 'type': 'int'},
        {'name': 'max_order_age', 'type': 'int'},
        {'name': 'order_price_refresh_tolerance_pct', 'type': 'float'},
        {'name': 'spread', 'type': 'json', 'format': '{"ASK": "float", "BID": "float"}'},
        {'name': 'order_amount', 'type': 'json', 'format': '{"ASK": "float", "BID": "float"}'},
        {'name': 'order_levels', 'type': 'json', 'format': '{"ASK": "int", "BID": "int"}'},
        {'name': 'order_level_amount', 'type': 'json', 'format': '{"ASK": "float", "BID": "float"}'},
        {'name': 'order_level_spread', 'type': 'json', 'format': '{"ASK": "float", "BID": "float"}'},
        ],
    'maker_hedge': [
        ],
    'vol': [
        {'name': 'lower_order_amount', 'type': 'float'},
        {'name': 'higher_order_amount', 'type': 'float'},
        {'name': 'price_band', 'type': 'float'},
        {'name': 'target_amount', 'type': 'float'},
        {'name': 'lower_order_time', 'type': 'int'},
        {'name': 'floating_price', 'type': 'bool'},
        {'name': 'inactivation_threshold', 'type': 'int'},
        ],
    'vol_lp': [
        {'name': 'lower_order_amount', 'type': 'float'},
        {'name': 'higher_order_amount', 'type': 'float'},
        {'name': 'target_amount', 'type': 'float'},
        {'name': 'lower_order_time', 'type': 'int'},
        {'name': 'inactivation_threshold', 'type': 'int'},
        {'name': 'threshold_percent_around_main_price', 'type': 'int'},
        ],
    'vol_clob': [
        ],
    'taker': [
        {'name': 'execution_side_type', 'type': 'str', 'values': ['ONLY_BUY', 'ONLY_SELL', 'BUY_OR_SELL', 'SELL_OR_BUY']},
        {'name': 'use_vwap', 'type': 'str', 'values': ['EXCHANGE', 'GENERAL', 'NONE']},
        {'name': 'vwap_price_factor', 'type': 'float'},
        {'name': 'min_order_amount', 'type': 'float'},
        {'name': 'max_order_amount', 'type': 'float'},
        {'name': 'limit_price', 'type': 'float'},
        {'name': 'only_price_opportunities', 'type': 'bool'},
        {'name': 'trade_amount_limit_1h', 'type': 'json', 'format': '{"SELL": "int", "BUY": "int"}'},
        ],
    'taker_clob': [
        ],
    'arbitrage': [
        {'name': 'min_profitability', 'type': 'float'},
        ],
    'arbitrage_triple': [
        {'name': 'min_profitability', 'type': 'float'},
        {'name': 'pivot_asset', 'type': 'str', 'values': ['BTC', 'ETH']},
        {'name': 'target', 'type': 'str', 'values': ['base', 'quote']},
        ],
    'turn': [
        ],
}

def bot_exist(bot_id: str, bot_type: str, region: str = None) -> bool:
    bot_group = get_bot_group(bot_type=bot_type)
    bot_config_file = '../' + bot_group + '_bots/' + bot_id + '/config.json'
    if region is None:
        return os.path.exists(bot_config_file)
    config = json.loads(open(bot_config_file, 'r', encoding='UTF-8').read())
    return config['region'] == region

def get_bot_group(bot_type: str):
    if bot_type == 'maker_clob' or bot_type == 'maker_hedge' or bot_type == 'maker':
        bot_group = 'maker'
    elif bot_type == 'taker_clob' or bot_type == 'taker':
        bot_group = 'taker'
    elif bot_type == 'vol_lp' or bot_type == 'vol_clob' or bot_type == 'vol':
        bot_group = 'vol'
    elif bot_type == 'arbitrage' or bot_type == 'arbitrage_triple':
        bot_group = 'arbitrage'
    elif bot_type == 'turn':
        bot_group = 'turn'
    return bot_group    

def get_bot_strategy(bot_id: str, bot_type: str) -> list:
    bot_group = get_bot_group(bot_type=bot_type)
    bot_config_file = '../' + bot_group + '_bots/' + bot_id + '/config.json'
    if os.path.exists(bot_config_file):
        return json.loads(open(bot_config_file, 'r', encoding='UTF-8').read())['strategy']
    return ''

def get_strategy_bots(strategy_id: str, strategy_type: str) -> list:
    bot_group = get_bot_group(bot_type=strategy_type)
    bots_folder = '../' + bot_group + '_bots'
    bots = []
    for bot_folder in os.listdir(bots_folder):
        bot_config_file = bots_folder + '/' + bot_folder + '/config.json'
        if os.path.exists(bot_config_file):
            with open(bot_config_file, "r", encoding='UTF-8') as jsonFile:
                bot_config = json.load(jsonFile)
                bot_config_strategy = bot_config['strategy']
                if strategy_id == bot_config_strategy:
                    bots.append(bot_config)
    return bots  

def add_new_attributes_values_to_bot_config(bot_id: str, bot_type: str, new_attributes_values: dict):
    attributes = ['strategy', 'base_asset', 'quote_asset']
    bot_group = get_bot_group(bot_type=bot_type)
    bot_config_file = '../' + bot_group + '_bots/' + bot_id + '/config.json'
    if os.path.exists(bot_config_file):
        config = json.loads(open(bot_config_file, 'r', encoding='UTF-8').read())
        if 'exchange' in config and 'api' in config:
            attributes.append('exchange')
            attributes.append('api')
        if 'connector' in config and 'wallet' in config:
            attributes.append('connector')
            attributes.append('wallet')
        for new_attribute in new_attributes_values:
            if new_attribute in attributes:
                config[new_attribute] = new_attributes_values[new_attribute]   
        config['bot_group'] = new_attributes_values['bot_group'] 
        return config
    return None 

def str_to_bool(s):
    if s == 'true':
         return True
    elif s == 'false':
         return False
    else:
         raise ValueError
     