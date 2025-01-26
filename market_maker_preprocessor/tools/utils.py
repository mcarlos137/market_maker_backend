import os
import json
import time
from datetime import datetime
from damexCommons.tools.utils import EXCHANGE_FOLDER, EXCHANGE_OLD_FOLDER, get_period_datetime

def get_new_file_time(file_time, period):
    selected_time = datetime.fromtimestamp(file_time / 1000)
    rounded_time = 0
    rounded_time = get_period_datetime(selected_time, period)
    if rounded_time == 0:
        return None
    new_file_time = int(rounded_time.timestamp() * 1000)
    return new_file_time


def get_new_file_data_for_pnl_values_ticker(data, data_type, operation, final_file):
    attribute_1 = None
    attribute_2 = None
    match operation:            
        case 'current_pnl':
            for value in data['values']:
                attribute_1 = 'type'
                attribute_2 = 'value'
        case 'current_values':
            for value in data['values']:
                attribute_1 = 'currenty'
                attribute_2 = 'amount'

    match(data_type):
        # =======SNAP CASE=======
        case 'snap':
            #print("====SNAP====")
            return data

        # =======INCR CASE=======
        case 'incr':
            #print("====INCR====")
            if os.path.exists(final_file):
                new_data = {
                    'time': data['time'],
                    'values': []
                }
                with open(final_file, 'r', encoding='UTF-8') as p:
                    previous_data = json.load(p)
                    for value in previous_data['values']:
                        # for every operation inside this loop you need to see the value in the data object
                        attribute_1_previous_value = value[attribute_1]
                        previous_values = [
                            x for x in data['values'] if x[attribute_1] == attribute_1_previous_value]
                        if len(previous_values) < 1:
                            continue                        
                        new_value = {attribute_1: attribute_1_previous_value,
                                     attribute_2: float((value[attribute_2])) + float((previous_values[0][attribute_2]))} 
                        new_data['values'].append((new_value))
                return new_data
            return data
        # =======AVG CASE=======
        case 'avg':
            #print("====AVG====")
            if os.path.exists(final_file):
                new_data = {
                    'time': data['time'],
                    'values': []
                }
                with open(final_file, 'r', encoding='UTF-8') as p:
                    previous_data = json.load(p)
                    for previous_value in previous_data['values']:
                        attribute_1_previous_value = previous_value[attribute_1]
                        new_values = [
                            x for x in data['values'] if x[attribute_1] == attribute_1_previous_value]
                        if len(new_values) < 1:
                            continue
                        summ = previous_value['sum'] + new_values[0][attribute_2]
                        count = previous_value['quantity'] + 1
                        new_value = {
                            attribute_1: attribute_1_previous_value,
                            attribute_2: float(summ / count),
                            'sum': summ,
                            'quantity': count
                        }
                        new_data['values'].append(new_value)
                return new_data
            new_data = {
                'time': data['time'],
                'values': []
            }
            for value in data['values']:
                new_value = {
                    attribute_1: value[attribute_1],
                    attribute_2: float(value[attribute_2]),
                    'sum': value[attribute_2],
                    'quantity': 1
                }
                new_data['values'].append(new_value)
            return new_data

def process_data(new_data, data, operation, data_type, period_in_minutes, attribute):
    bid_value = 0
    ask_value = 0
    buy_value = 0
    sell_value = 0
    bid_count = 0
    ask_count = 0
    buy_count = 0
    sell_count = 0
    for d in data:
        match str(d['order_side']).upper():
            case 'BID':
                bid_value += add_value(operation, d)
                bid_count += 1
            case 'ASK':
                ask_value += add_value(operation, d)
                ask_count += 1
            case 'BUY':
                buy_value += add_value(operation, d)
                buy_count += 1
            case 'SELL':
                sell_value += add_value(operation, d)
                sell_count += 1
        
    if operation == 'current_orders_mid_prices':
        if bid_count > 0:
            bid_value = bid_value / bid_count
        if ask_count > 0:
            ask_value = ask_value / ask_count
        if buy_count > 0:
            buy_value = buy_value / buy_count
        if sell_count > 0:
            sell_value = sell_value / sell_count
                        
    if data_type == 'avg' and operation != 'current_orders_mid_prices':
        bid_value = bid_value / period_in_minutes
        ask_value = ask_value / period_in_minutes
        buy_value = buy_value / period_in_minutes
        sell_value = sell_value / period_in_minutes
        
    new_data['values'] = [
        {'operation': 'BID' if operation != 'current_orders_mid_prices' else 'BID__MID', attribute: bid_value},
        {'operation': 'ASK' if operation != 'current_orders_mid_prices' else 'ASK__MID', attribute: ask_value},
        {'operation': 'BUY' if operation != 'current_orders_mid_prices' else 'BUY__MID', attribute: buy_value},
        {'operation': 'SELL' if operation != 'current_orders_mid_prices' else 'SELL__MID', attribute: sell_value},
    ]
        
    if operation == 'current_orders_mid_prices':
        bid_best = 0
        ask_best = 0
        buy_best = 0
        sell_best = 0
        for d in data:
            if str(d['order_side']).upper() == 'BID' and (bid_best == 0 or bid_best < float(d['price'])):
                bid_best = float(d['price'])
            if str(d['order_side']).upper() == 'ASK' and (ask_best == 0 or ask_best > float(d['price'])):
                ask_best = float(d['price'])
            
            if str(d['order_side']).upper() == 'BUY' and (buy_best == 0 or buy_best < float(d['price'])):
                buy_best = float(d['price'])
            if str(d['order_side']).upper() == 'SELL' and (sell_best == 0 or sell_best > float(d['price'])):
                sell_best = float(d['price'])
                              
        new_data['values'].append({'operation': 'BID__BEST', attribute: bid_best})
        new_data['values'].append({'operation': 'ASK__BEST', attribute: ask_best})
        new_data['values'].append({'operation': 'BUY__BEST', attribute: buy_best})
        new_data['values'].append({'operation': 'SELL__BEST', attribute: sell_best})
            
    return new_data

def add_value(operation, data):
    match operation:
        case 'current_orders_count':
            return 1
        case 'current_orders_amounts':
            return float(data['amount'])
        case 'current_orders_mid_prices':
            return float(data['price'])

def get_current_time():
    raw_time = int(time.time() * 1e3)
    i = 0
    current_time = None
    while i < 4:
        compare_time = int(datetime.now().replace(second=(15 * i), microsecond=0).timestamp() * 1000)
        if (raw_time - compare_time) < 15000:
            #Delaying the current time 15 seconds to be flexible
            current_time = compare_time - 15000
            break
        i = i + 1
    return current_time

def get_pnl_values(data_set, look_previous_data, all_in_one_exchange_market):
    data = {}
    #fee_factor = 0.001
    fee_factor = 0
    exchange = None
    market = None
    exchange_market = None

    for row in data_set:
        exchange = str(row[6].replace(' ', '_')).lower()
        market = row[0] + '-' + row[1]
        exchange_market = exchange + '__' + market
        
        if all_in_one_exchange_market:
            exchange_market = 'ALL_IN_ONE'
            
        if not exchange_market in data:
            data[exchange_market] = {
                'position': 0,
                'position_shifted': 0,
                'vwap': None,
                'realized_pnl_sum': 0,
                'unrealized_pnl': 0,
                'total_pnl': 0,
            }
        if look_previous_data:
            info_file_path = EXCHANGE_FOLDER + '/' + exchange + '/current_pnl/' + market + '/info.json'
            market_operation_exchange_folder = EXCHANGE_FOLDER + '/' + exchange + '/' + 'current_pnl' + '/' + market
            market_operation_exchange_old_folder = EXCHANGE_OLD_FOLDER + '/' + exchange + '/' + 'current_pnl' + '/' + market
            if os.path.exists(info_file_path):
                info = json.loads(open(info_file_path, 'r', encoding='UTF-8').read())
                # print('info', info['last_file_name'])
                if not 'reset' in info:
                    pnl_file_path = market_operation_exchange_folder + \
                        '/' + info['last_file_name']
                    if not os.path.exists(pnl_file_path):
                        pnl_file_path = market_operation_exchange_old_folder + \
                            '/' + info['last_file_name']
                    data_previous = json.loads(
                        open(pnl_file_path, 'r', encoding='UTF-8').read())
                    # print('data_previous', data_previous)
                    data[exchange_market]['position'] = data_previous['values'][0]['value']
                    data[exchange_market]['position_shifted'] = data_previous['values'][1]['value']
                    data[exchange_market]['vwap'] = data_previous['values'][2]['value']
                    data[exchange_market]['realized_pnl_sum'] = data_previous['values'][3]['value']
                else:
                    print('delete reset_current_pnl from info.json')
                    del info['reset']
                    with open(info_file_path, "w", encoding='UTF-8') as jsonFile:
                        json.dump(info, jsonFile)

    for row in data_set:
        # print('trade', row)
        market = row[0] + '-' + row[1]

        trade_type = str(row[2]).upper()
        amount = row[3] / 1e6
        price = row[4] / 1e6
        # fee = row[5]
        fee = amount * price * fee_factor

        exchange = str(row[6].replace(' ', '_')).lower()
        exchange_market = exchange + '__' + market

        if all_in_one_exchange_market:
            exchange_market = 'ALL_IN_ONE'

        if data[exchange_market]['vwap'] is None:
            data[exchange_market]['vwap'] = price
                        
        data[exchange_market]['position_shifted'] = data[exchange_market]['position']

        if trade_type == 'BUY':

            data[exchange_market]['position'] += amount * (1 - fee_factor)

            if data[exchange_market]['position_shifted'] > 0.00001:
                data[exchange_market]['vwap'] = (data[exchange_market]['vwap'] * data[exchange_market]
                                                 ['position_shifted'] + (amount * price) + fee) / (data[exchange_market]['position'])
                data[exchange_market]['realized_pnl_sum'] = data[exchange_market]['realized_pnl_sum']
            
            elif data[exchange_market]['position_shifted'] < -0.00001:
                data[exchange_market]['vwap'] = data[exchange_market]['vwap']
                data[exchange_market]['realized_pnl_sum'] += (data[exchange_market]['vwap'] - price) * amount
            
            else:
                data[exchange_market]['vwap'] = price

        if trade_type == 'SELL':

            data[exchange_market]['position'] -= amount

            if data[exchange_market]['position_shifted'] < -0.00001:
                data[exchange_market]['vwap'] = (abs(data[exchange_market]['vwap'] * data[exchange_market]
                                                 ['position_shifted']) + (amount * price) + fee) / abs(data[exchange_market]['position'])
                data[exchange_market]['realized_pnl_sum'] = data[exchange_market]['realized_pnl_sum'] + 0

            elif data[exchange_market]['position_shifted'] > 0.00001:
                data[exchange_market]['vwap'] = data[exchange_market]['vwap']
                data[exchange_market]['realized_pnl_sum'] += (price - data[exchange_market]['vwap']) * amount
                
            else:
                data[exchange_market]['vwap'] = price
                
    current_price = get_ticker_last_price(exchange=exchange, market=market)

    data[exchange_market]['unrealized_pnl'] = (current_price - data[exchange_market]['vwap']) * data[exchange_market]['position']

    data[exchange_market]['total_pnl'] = data[exchange_market]['realized_pnl_sum'] + \
        data[exchange_market]['unrealized_pnl']

    #print('data-------->', data)

    return data

def get_ticker_last_price(exchange, market):
    exchange = exchange.replace('_paper_trade', '')
    exchange_folder = EXCHANGE_FOLDER + '/' + exchange
    operation_exchange_folder = exchange_folder + '/ticker'
    market_operation_exchange_folder = operation_exchange_folder + '/' + market
    info = json.loads(
        open(market_operation_exchange_folder + '/info.json', 'r', encoding='UTF-8').read())
    # print('info', info['last_file_name'])
    data = json.loads(open(market_operation_exchange_folder + '/' + info['last_file_name'], 'r', encoding='UTF-8').read())
    # print('data', data)
    return float(data['lastPrice'])

