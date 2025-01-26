import os
import json
import time
import logging
import sys
from datetime import datetime, timedelta
from damexCommons.tools.utils import BASE_PATH

def emulated_balance_evaluate_trades(emulated_balance_name: str, type: str, profit_asset: str, profit_extra: float, final_time: int = None):
    trades_size = None
    match type:
        case 'arbitrage_simple':
            trades_size = 2
        case 'arbitrage_triple':
            trades_size = 3
    emulated_balance_folder = BASE_PATH + '/base/emulated_balances/' + emulated_balance_name
    i = 0
    balance_diff = {}
    balance_diff_by_exchange = {}
    emulated_balance_old_files = []
    emulated_balance_new_files = []
    emulated_balance_files = []
    emulated_balance_files_out_of_time = []
    type_emulated_balance_folder = emulated_balance_folder + '/' + 'trades'
    type_emulated_balance_old_folder = type_emulated_balance_folder + '/' + 'old'
    if os.path.isdir(type_emulated_balance_old_folder):
        for emulated_balance_old_file in os.listdir(type_emulated_balance_old_folder):
            emulated_balance_old_file = type_emulated_balance_old_folder + '/' + emulated_balance_old_file
            if not os.path.isfile(emulated_balance_old_file):
                continue
            emulated_balance_old_files.append(emulated_balance_old_file)
    emulated_balance_old_files = sorted(emulated_balance_old_files)
    for emulated_balance_file in os.listdir(type_emulated_balance_folder):
        if emulated_balance_file == 'old':
            continue
        if final_time is not None and int(emulated_balance_file.replace('.json', '')) > final_time:
            emulated_balance_files_out_of_time.append(emulated_balance_file)
            print('----------------', emulated_balance_file, final_time)
            continue
        emulated_balance_file = type_emulated_balance_folder + '/' + emulated_balance_file
        if not os.path.isfile(emulated_balance_file):
            continue
        emulated_balance_new_files.append(emulated_balance_file)
    emulated_balance_new_files = sorted(emulated_balance_new_files)
        
    emulated_balance_files.extend(emulated_balance_old_files)
    emulated_balance_files.extend(emulated_balance_new_files)
    
    emulated_balance_files_out_of_time = sorted(emulated_balance_files_out_of_time)

    volume_total_passet = 0
    previous_passet = 0
    previous_emulated_balances = []
    trades_extra_profit = []
    trades_by_side_count = {}
    profit_max_passet = 0
    profit_ranges_passet = {'0-1': 0, '1-2': 0, '2-3': 0, '3-4': 0, '4-5': 0, '5-6': 0, '6-7': 0, '7-8': 0, '8-9': 0, '9-10': 0, '10-15': 0, '15-20': 0, '20-25': 0, '25-30': 0, '30-50': 0, '50-100': 0, '100-200': 0, '200-500': 0,'500-1000': 0 }
    initial_time = None
    for emulated_balance_file in emulated_balance_files:
        print('emulated_balance_file', emulated_balance_file)
        emulated_balance = json.loads(open(emulated_balance_file, 'r', encoding='UTF-8').read())
        if 'consolidated' in emulated_balance and emulated_balance['consolidated']:
            print('consolidated---------------', emulated_balance_file)
            continue
        if len(emulated_balance['values']) < 2:
            break
        if initial_time is None:
            initial_time = emulated_balance['time']
        if emulated_balance['exchange'] not in trades_by_side_count:
            trades_by_side_count[emulated_balance['exchange']] = {'BUY': 0, 'SELL': 0}
        if emulated_balance['exchange'] not in balance_diff_by_exchange:
            balance_diff_by_exchange[emulated_balance['exchange']] = {}
        for value in emulated_balance['values']:
            asset = value['asset']
            amount = value['amount']
            if asset not in balance_diff:
                balance_diff[asset] = 0
            balance_diff[asset] += amount
            if emulated_balance['exchange'] not in balance_diff_by_exchange:
                balance_diff_by_exchange[emulated_balance['exchange']] = {}
            if asset not in balance_diff_by_exchange[emulated_balance['exchange']]:
                balance_diff_by_exchange[emulated_balance['exchange']][asset] = 0
            balance_diff_by_exchange[emulated_balance['exchange']][asset] += amount
            if asset == profit_asset:
                volume_total_passet += abs(amount)
                if amount > 0:
                    trades_by_side_count[emulated_balance['exchange']]['SELL'] += 1
                else:
                    trades_by_side_count[emulated_balance['exchange']]['BUY'] += 1
        i += 1
        
        previous_emulated_balances.append(emulated_balance)
        if i % trades_size == 0: 
            previous_passet = 0
            last_passet = 0
            for value in previous_emulated_balances[0]['values']:
                if value['asset'] == profit_asset:
                    previous_passet = value['amount']
                    break
            for value in previous_emulated_balances[trades_size - 1]['values']:
                if value['asset'] == profit_asset:
                    last_passet = value['amount']
                    break
            profit = last_passet + previous_passet
            if profit > 100:
                print('--------->', profit, last_passet, previous_passet)
                break
            if profit_max_passet < profit:
                profit_max_passet = profit
            for profit_range in profit_ranges_passet:
                range_low = float(profit_range.split('-')[0])
                range_high = float(profit_range.split('-')[1])
                if profit < range_high and profit >= range_low:
                    profit_ranges_passet[profit_range] += 1
                    break
            if profit > profit_extra:
                if trades_size == 3:
                    trade_extra_profit = {
                        'trade_1': previous_emulated_balances[0],
                        'trade_2': previous_emulated_balances[1],
                        'trade_3': previous_emulated_balances[2],
                        'profit': profit
                    }
                elif trades_size == 2:
                    trade_extra_profit = {
                        'trade_1': previous_emulated_balances[0],
                        'trade_2': previous_emulated_balances[1],
                        'profit': profit
                    }
                trades_extra_profit.append(trade_extra_profit)
            previous_emulated_balances = []
                
    if trades_size == 3:
        volume_total_passet *= 1.5
        for exchange in trades_by_side_count:
            trades_by_side_count[exchange]['BUY'] *= 1.5 
            trades_by_side_count[exchange]['SELL'] *= 1.5 
    
    emulated_balance_config_file = emulated_balance_folder + '/config.json'
    emulated_balance_config = json.loads(open(emulated_balance_config_file, 'r', encoding='UTF-8').read())
    
    current_time = time.time()
    data = {
        'initial_timestamp': str(datetime.fromtimestamp(initial_time / 1e3)),
        'current_timestamp': str(datetime.fromtimestamp(current_time)),
        'time_period': str(timedelta(milliseconds=current_time * 1e3 - initial_time)),
        'balance_initial': emulated_balance_config['initial'],
        'balance_diff': balance_diff,
        'balance_diff_by_exchange': balance_diff_by_exchange,
        'balance_current': emulated_balance_config['current'],
        'profit_max_passet': profit_max_passet,
        'profit_ranges_passet': profit_ranges_passet,
        'trades_count': int(i / trades_size),
        'trades_extra_profit': trades_extra_profit,
        'trades_by_side_count': trades_by_side_count,
        'volume_total_passet': volume_total_passet,
        #'trades_out_of_final_time': emulated_balance_files_out_of_time
    }
    return data

                            
result = emulated_balance_evaluate_trades(emulated_balance_name=sys.argv[1], type=sys.argv[2], profit_asset=sys.argv[3], profit_extra=float(sys.argv[4]))

print('result', result)