import os
import json
import shutil
import sys
sys.path.append(os.getcwd())
from tools.utils import get_new_file_time
from damexCommons.tools.utils import BASE_PATH

files_to_evaluate_count = int(sys.argv[1])

PERIODS = ['1m', '5m', '15m', '30m', '1h', '4h', '12h', '24h']

FOLDERS_TO_WATCH = [
    BASE_PATH + '/arbitrage_opportunities/simple', 
    #BASE_PATH + '/arbitrage_opportunities/triple'
]

arbitrage_opportunity_files = []

for folder_to_watch in FOLDERS_TO_WATCH:
    for arbitrage_opportunity_file in os.listdir(folder_to_watch):
        arbitrage_opportunity_file = folder_to_watch + '/' + arbitrage_opportunity_file
        if not os.path.isfile(arbitrage_opportunity_file):
            continue
        if 'info.json' in arbitrage_opportunity_file:
            continue
        arbitrage_opportunity_files.append(arbitrage_opportunity_file)
        
arbitrage_opportunity_files = sorted(arbitrage_opportunity_files)

print('arbitrage_opportunity_files len', len(arbitrage_opportunity_files))

arbitrage_opportunities = {}

move_to_old_files = []

i = 0
for arbitrage_opportunity_file in arbitrage_opportunity_files:
    arbitrage_opportunity = json.loads(open(arbitrage_opportunity_file, 'r', encoding='UTF-8').read())
    file_time = int(arbitrage_opportunity_file.split('/')[5].replace('.json', ''))
    arbitrage_opportunity_type_folder = arbitrage_opportunity_file.replace(arbitrage_opportunity_file.split('/')[5], '')
    for period in PERIODS:
        new_file_time = get_new_file_time(file_time=file_time, period=period)
        arbitrage_opportunity_type_period_folder = arbitrage_opportunity_type_folder + period
        if not os.path.exists(arbitrage_opportunity_type_period_folder):
            os.makedirs(arbitrage_opportunity_type_period_folder)
        arbitrage_opportunity_type_file = arbitrage_opportunity_type_folder + period + '/' + str(new_file_time) + '.json'

        if arbitrage_opportunity_type_file not in arbitrage_opportunities:
            if not os.path.isfile(arbitrage_opportunity_type_file):
                arbitrage_opportunities[arbitrage_opportunity_type_file] = {}
            else:
                arbitrage_opportunities[arbitrage_opportunity_type_file] = json.loads(open(arbitrage_opportunity_type_file, 'r', encoding='UTF-8').read())
        for key in arbitrage_opportunity:
            if key not in arbitrage_opportunities[arbitrage_opportunity_type_file]:
                arbitrage_opportunities[arbitrage_opportunity_type_file][key] = {
                    'init_time': arbitrage_opportunity[key]['init_time'],
                    'last_time': arbitrage_opportunity[key]['last_time'],
                    'period_in_secs': int((arbitrage_opportunity[key]['last_time'] - arbitrage_opportunity[key]['init_time']) / 1e3),
                    'count': 1,
                    'max_amount': {
                        'profitability_percentage': arbitrage_opportunity[key]['profitability_percentage'],
                        'depth': arbitrage_opportunity[key]['depth'],
                        'profitability_amount': arbitrage_opportunity[key]['profitability_amount'],
                    },
                    'max_percentage': {
                        'profitability_percentage': arbitrage_opportunity[key]['profitability_percentage'],
                        'depth': arbitrage_opportunity[key]['depth'],
                        'profitability_amount': arbitrage_opportunity[key]['profitability_amount'],
                    },
                    'max_depth': {
                        'profitability_percentage': arbitrage_opportunity[key]['profitability_percentage'],
                        'depth': arbitrage_opportunity[key]['depth'],
                        'profitability_amount': arbitrage_opportunity[key]['profitability_amount'],
                    },
                    'profitability_asset': arbitrage_opportunity[key]['profitability_asset']
                }
            if arbitrage_opportunity[key]['init_time'] == arbitrage_opportunities[arbitrage_opportunity_type_file][key]['init_time']:
                arbitrage_opportunities[arbitrage_opportunity_type_file][key]['period_in_secs'] += int((arbitrage_opportunity[key]['last_time'] - arbitrage_opportunities[arbitrage_opportunity_type_file][key]['last_time']) / 1e3)
            else:
                arbitrage_opportunities[arbitrage_opportunity_type_file][key]['period_in_secs'] += int((arbitrage_opportunity[key]['last_time'] - arbitrage_opportunity[key]['init_time']) / 1e3)
                arbitrage_opportunities[arbitrage_opportunity_type_file][key]['count'] += 1
                
            arbitrage_opportunities[arbitrage_opportunity_type_file][key]['init_time'] = arbitrage_opportunity[key]['init_time']
            arbitrage_opportunities[arbitrage_opportunity_type_file][key]['last_time'] = arbitrage_opportunity[key]['last_time']
            
            if arbitrage_opportunities[arbitrage_opportunity_type_file][key]['max_amount']['profitability_amount'] < arbitrage_opportunity[key]['profitability_amount']:
                arbitrage_opportunities[arbitrage_opportunity_type_file][key]['max_amount']['profitability_percentage'] = arbitrage_opportunity[key]['profitability_percentage']
                arbitrage_opportunities[arbitrage_opportunity_type_file][key]['max_amount']['depth'] = arbitrage_opportunity[key]['depth']
                arbitrage_opportunities[arbitrage_opportunity_type_file][key]['max_amount']['profitability_amount'] = arbitrage_opportunity[key]['profitability_amount']
                
            if arbitrage_opportunities[arbitrage_opportunity_type_file][key]['max_percentage']['profitability_percentage'] < arbitrage_opportunity[key]['profitability_percentage']:
                arbitrage_opportunities[arbitrage_opportunity_type_file][key]['max_percentage']['profitability_percentage'] = arbitrage_opportunity[key]['profitability_percentage']
                arbitrage_opportunities[arbitrage_opportunity_type_file][key]['max_percentage']['depth'] = arbitrage_opportunity[key]['depth']
                arbitrage_opportunities[arbitrage_opportunity_type_file][key]['max_percentage']['profitability_amount'] = arbitrage_opportunity[key]['profitability_amount']
            
            if arbitrage_opportunities[arbitrage_opportunity_type_file][key]['max_depth']['depth'] < arbitrage_opportunity[key]['depth']:
                arbitrage_opportunities[arbitrage_opportunity_type_file][key]['max_depth']['profitability_percentage'] = arbitrage_opportunity[key]['profitability_percentage']
                arbitrage_opportunities[arbitrage_opportunity_type_file][key]['max_depth']['depth'] = arbitrage_opportunity[key]['depth']
                arbitrage_opportunities[arbitrage_opportunity_type_file][key]['max_depth']['profitability_amount'] = arbitrage_opportunity[key]['profitability_amount']
                
    move_to_old_files.append(arbitrage_opportunity_file)
    
    i += 1
    if i >= files_to_evaluate_count:
        break

for key in arbitrage_opportunities:
    print('arbitrage_opportunity----------', key, arbitrage_opportunities[key])
    f = open( key, 'w+', encoding='UTF-8')
    f.write( json.dumps(arbitrage_opportunities[key]) )
    f.close()

for move_to_old_file in move_to_old_files:
    move_to_old_file_new = move_to_old_file.replace(move_to_old_file.split('/')[5], '') + 'old/' + move_to_old_file.split('/')[5]
    print('move_to_old_file------------', move_to_old_file)
    print('move_to_old_file_new------------', move_to_old_file_new)
    try:
        shutil.move(move_to_old_file, move_to_old_file_new)
        print('move_file')
    except (Exception) as error:
        print("Error while moving file", error)
