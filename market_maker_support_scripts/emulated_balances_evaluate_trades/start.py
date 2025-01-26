import os
import sys
import json
import datetime

def run(emulated_balance_name: str, quote_asset: str, extra_profit: int):
    emulated_balance_folder = '/home/ubuntu/base/emulated_balances/' + emulated_balance_name
    i = 0
    balance_diff = {}
    balance_diff_by_exchange = {}
    emulated_balance_old_files = []
    emulated_balance_new_files = []
    emulated_balance_files = []
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
        emulated_balance_file = type_emulated_balance_folder + '/' + emulated_balance_file
        if not os.path.isfile(emulated_balance_file):
            continue
        emulated_balance_new_files.append(emulated_balance_file)
    emulated_balance_new_files = sorted(emulated_balance_new_files)
        
    emulated_balance_files.extend(emulated_balance_old_files)
    emulated_balance_files.extend(emulated_balance_new_files)

    volume_total_usdt = 0
    previous_usdt = 0
    previous_emulated_balance = None
    trades_extra_profit = []
    trades_by_side_count = {}
    profit_max_usdt = 0
    exchanges = set()
    profit_ranges_usdt = {'0-1': 0, '1-2': 0, '2-3': 0, '3-4': 0, '4-5': 0, '5-6': 0, '6-7': 0, '7-8': 0, '8-9': 0, '9-10': 0, '10-15': 0, '15-20': 0, '20-25': 0, '25-30': 0, '30-50': 0, '50-100': 0, '100-200': 0, '200-500': 0,'500-1000': 0 }
    j = 0
    initial_time = None
    final_time = None
    for emulated_balance_file in emulated_balance_files:
        emulated_balance = json.loads(open(emulated_balance_file, 'r', encoding='UTF-8').read())
        if 'consolidated' in emulated_balance and emulated_balance['consolidated']:
            continue
        if len(emulated_balance['values']) < 2:
            break
        if initial_time is None:
            initial_time = emulated_balance['time']
        if emulated_balance['exchange'] not in trades_by_side_count:
            trades_by_side_count[emulated_balance['exchange']] = {'BUY': 0, 'SELL': 0}
        if emulated_balance['exchange'] not in balance_diff_by_exchange:
            balance_diff_by_exchange[emulated_balance['exchange']] = {}
        exchanges.add(emulated_balance['exchange'])
        final_time = emulated_balance['time']
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
            if asset == 'USDT':
                volume_total_usdt += abs(amount)
                if amount > 0:
                    trades_by_side_count[emulated_balance['exchange']]['SELL'] += 1
                else:
                    trades_by_side_count[emulated_balance['exchange']]['BUY'] += 1
        i += 1
        if i % 2 == 0: 
            profit = balance_diff[quote_asset] - previous_usdt
            #print('total', total, i, profit)
            previous_usdt = balance_diff[quote_asset]
            if profit_max_usdt < profit:
                profit_max_usdt = profit
            for profit_range in profit_ranges_usdt:
                range_low = float(profit_range.split('-')[0])
                range_high = float(profit_range.split('-')[1])
                if profit < range_high and profit >= range_low:
                    profit_ranges_usdt[profit_range] += 1
                    break
            if profit > extra_profit:
                j += 1
                trade_extra_profit = {
                    'trade_1': previous_emulated_balance,
                    'trade_2': emulated_balance,
                    'profit': profit
                }
                trades_extra_profit.append(trade_extra_profit)
                #sys.exit(-1)
        previous_emulated_balance = emulated_balance
        
    #print('initial_time', initial_time)
    #print('final_time', final_time)
    data = {
        'time_period': str(datetime.timedelta(milliseconds=final_time - initial_time)),
        'exchanges': exchanges,
        'balance_diff': balance_diff,
        'balance_diff_by_exchange': balance_diff_by_exchange,
        'profit_max_usdt': profit_max_usdt,
        'profit_ranges_usdt': profit_ranges_usdt,
        'trades_count': int(i / 2),
        'trades_extra_profit': trades_extra_profit,
        'trades_by_side_count': trades_by_side_count,
        'volume_total_usdt': volume_total_usdt
    }
    print('initial time', initial_time)
    print('time period', data['time_period'])
    print('exchanges', data['exchanges'])
    print('balance diff', data['balance_diff'])    
    print('balance diff by exchange', data['balance_diff_by_exchange'])    
    print('profit max (USDT)', data['profit_max_usdt'])
    print('profit ranges (USDT)', data['profit_ranges_usdt'])
    print('trades count', data['trades_count'])
    print('trade extra profit count', data['trades_extra_profit'], len(data['trades_extra_profit']))
    print('trades by side count', data['trades_by_side_count'])
    print('volume total (USDT)', data['volume_total_usdt'])
                
run(emulated_balance_name=sys.argv[1], quote_asset=sys.argv[2] , extra_profit=int(sys.argv[3]))
        