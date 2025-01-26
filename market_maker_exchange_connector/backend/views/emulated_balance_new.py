import json
import time
import os
import shutil
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

@api_view(['POST'])
@permission_classes([AllowAny])
def add(request):
    if not 'name' in request.data:
        return Response('request must has param name', status=status.HTTP_400_BAD_REQUEST)
    if not 'exchange' in request.data:
        return Response('request must has param exchange', status=status.HTTP_400_BAD_REQUEST)
    if not 'asset' in request.data:
        return Response('request must has param asset', status=status.HTTP_400_BAD_REQUEST)
    if not 'amount' in request.data:
        return Response('request must has param amount', status=status.HTTP_400_BAD_REQUEST)

    name = request.data['name']
    exchange = request.data['exchange']
    asset = request.data['asset']
    amount = float(request.data['amount'])

    emulated_balances_folder = '../base/emulated_balances'        
    emulated_balance_folder = emulated_balances_folder + '/' + name
    emulated_balance_config_file = emulated_balances_folder + '/' + name + '/config.json'
    
    emulated_balance_config = None
    if not os.path.isdir(emulated_balance_folder):
        os.makedirs(emulated_balance_folder)
        os.makedirs(emulated_balance_folder + '/orders')
        os.makedirs(emulated_balance_folder + '/trades')
        os.makedirs(emulated_balance_folder + '/deposits')
        os.makedirs(emulated_balance_folder + '/withdrawals')
        emulated_balance_config = {
            'name': name, 
            'initial': {
                exchange: {
                    asset: {
                        'available': amount,
                        'total': amount
                    }
                }
            },
            'current': {
                exchange: {
                    asset: {
                        'available': amount,
                        'total': amount
                    }
                }
            }
        }
    else:
        emulated_balance_config = json.loads(open(emulated_balance_config_file, 'r', encoding='UTF-8').read())
        if exchange in emulated_balance_config['initial'] and exchange in emulated_balance_config['current'] and emulated_balance_config['initial'][exchange] != emulated_balance_config['current'][exchange]:
            return Response('balance can not be modified if INITIAL and CURRENT are different. Reset values first')
        if exchange not in emulated_balance_config['initial']:
             emulated_balance_config['initial'][exchange] = {}
        emulated_balance_config['initial'][exchange][asset] = {'available': amount, 'total': amount}
        if exchange not in emulated_balance_config['current']:
             emulated_balance_config['current'][exchange] = {}
        emulated_balance_config['current'][exchange][asset] = {'available': amount, 'total': amount}
    
    if emulated_balance_config is None:
        return Response('FAILED')
    
    f = open( emulated_balance_config_file, 'w+', encoding='UTF-8')
    f.write( json.dumps(emulated_balance_config) )
    f.close()                    
    return Response('OK')


@api_view(['GET'])
@permission_classes([AllowAny])
def fetch(request):
    name = None
    if 'name' in request.GET:
        name = request.GET.get("name")
    emulated_balances = []
    emulated_balances_folder = '../base/emulated_balances'
    if name is not None:
        emulated_balance_config_file = emulated_balances_folder + '/' + name + '/config.json'
        if not os.path.exists(emulated_balance_config_file):
            return Response(emulated_balances)   
        emulated_balances.append(json.loads(open(emulated_balance_config_file, 'r', encoding='UTF-8').read()))
    else:
        for name in os.listdir(emulated_balances_folder):
            emulated_balance_folder = emulated_balances_folder + '/' + name
            if not os.path.isdir(emulated_balance_folder):
                continue
            emulated_balance_config_file = emulated_balance_folder + '/config.json'
            emulated_balances.append(json.loads(open(emulated_balance_config_file, 'r', encoding='UTF-8').read()))
            
    for emulated_balance in emulated_balances:
        
        emulated_balance_types = ['initial', 'current']
        for emulated_balance_type in emulated_balance_types:
            total_by_asset = {}
            for exchange in emulated_balance[emulated_balance_type]:
                for asset in emulated_balance[emulated_balance_type][exchange]:            
                    if asset not in total_by_asset:
                        total_by_asset[asset] = {'available': 0, 'total': 0}
                    total_by_asset[asset]['available'] +=  emulated_balance[emulated_balance_type][exchange][asset]['available']
                    total_by_asset[asset]['total'] +=  emulated_balance[emulated_balance_type][exchange][asset]['total']
            emulated_balance[emulated_balance_type]['total'] = total_by_asset
        
    return Response(emulated_balances)    
         

@api_view(['POST'])
@permission_classes([AllowAny])
def reset(request):
    if not 'name' in request.data:
        return Response('request must has param name', status=status.HTTP_400_BAD_REQUEST)
        
    name = request.data['name']
    
    current_time = int(time.time() * 1000)
    emulated_balances_folder = '../base/emulated_balances'        
    emulated_balance_folder = emulated_balances_folder + '/' + name
    
    emulated_balance_orders_folder = emulated_balance_folder + '/orders'
    emulated_balance_orders_old_folder = emulated_balance_orders_folder + '/' + str(current_time) 
    
    emulated_balance_trades_folder = emulated_balance_folder + '/trades'
    emulated_balance_trades_old_folder = emulated_balance_trades_folder + '/' + str(current_time) 
    
    emulated_balance_deposits_folder = emulated_balance_folder + '/deposits'
    emulated_balance_deposits_old_folder = emulated_balance_deposits_folder + '/' + str(current_time) 
    
    emulated_balance_withdrawals_folder = emulated_balance_folder + '/withdrawals'
    emulated_balance_withdrawals_old_folder = emulated_balance_withdrawals_folder + '/' + str(current_time) 
    
    os.makedirs(emulated_balance_orders_old_folder)
    os.makedirs(emulated_balance_trades_old_folder)
    os.makedirs(emulated_balance_deposits_old_folder)
    os.makedirs(emulated_balance_withdrawals_old_folder)
    
    move_folders = [
        [emulated_balance_orders_folder, emulated_balance_orders_old_folder],
        [emulated_balance_trades_folder, emulated_balance_trades_old_folder],
        [emulated_balance_deposits_folder, emulated_balance_deposits_old_folder],
        [emulated_balance_withdrawals_folder, emulated_balance_withdrawals_old_folder],
    ]
    
    for move_folder in move_folders: 
        for path_name in os.listdir(move_folder[0]):
            complete_path_name = move_folder[0] + '/' + path_name
            complete_path_name_old = move_folder[1] + '/' + path_name
            if os.path.isdir(complete_path_name):
                continue    
            try:
                shutil.move(complete_path_name, complete_path_name_old)
                print('move_file')
            except (Exception) as error:
                print("Error while moving file", error)
            
    emulated_balances_folder = '../base/emulated_balances'        
    emulated_balance_folder = emulated_balances_folder + '/' + name
    emulated_balance_config_file = emulated_balances_folder + '/' + name + '/config.json'
    emulated_balance_config = json.loads(open(emulated_balance_config_file, 'r', encoding='UTF-8').read())    
    
    emulated_balance_config['current'] = emulated_balance_config['initial']
        
    f = open( emulated_balance_config_file, 'w+', encoding='UTF-8')
    f.write( json.dumps(emulated_balance_config) )
    f.close()     
        
    return Response('OK')

         
@api_view(['POST'])
@permission_classes([AllowAny])
def execute(request):
    if not 'name' in request.data:
        return Response('request must has param name', status=status.HTTP_400_BAD_REQUEST)
    if not 'exchange' in request.data:
        return Response('request must has param exchange', status=status.HTTP_400_BAD_REQUEST)
    if not 'asset' in request.data:
        return Response('request must has param asset', status=status.HTTP_400_BAD_REQUEST)
    if not 'amount' in request.data:
        return Response('request must has param amount', status=status.HTTP_400_BAD_REQUEST)
    if not 'operation' in request.data:
        return Response('request must has param operation', status=status.HTTP_400_BAD_REQUEST)
        
    operation = request.data['operation']
        
    if operation == 'trade':    
        if not 'asset_turn' in request.data:
            return Response('request must has param asset_turn', status=status.HTTP_400_BAD_REQUEST)
        if not 'amount_turn' in request.data:
            return Response('request must has param amount_turn', status=status.HTTP_400_BAD_REQUEST)
                
    name = request.data['name']
    exchange = request.data['exchange']
    asset = request.data['asset']
    amount = request.data['amount']
        
    emulated_balances_folder = '../base/emulated_balances'        
    emulated_balance_folder = emulated_balances_folder + '/' + name
    if not os.path.isdir(emulated_balance_folder):
        return Response('emulated balance does not exist', status=status.HTTP_400_BAD_REQUEST)
        
    emulated_balance_folder = emulated_balances_folder + '/' + name
    emulated_balance_config_file = emulated_balances_folder + '/' + name + '/config.json'
    emulated_balance_config = json.loads(open(emulated_balance_config_file, 'r', encoding='UTF-8').read())   
        
    current_time = int(time.time() * 1000)
    operation_folder_name = operation.split('_')[0] + 's'
    
    emulated_balance = {'time': current_time, 'exchange': exchange, 'values': [], 'operation': operation}        
    emulated_balance_file = emulated_balance_folder + '/' + operation_folder_name + '/' + str(current_time) + '.json'
        
    match operation:
        case 'trade':
            asset_turn = request.data['asset_turn']
            amount_turn = request.data['amount_turn']            
            emulated_balance['values'].append({'asset': asset, 'amount': -1 * amount})
            emulated_balance['values'].append({'asset': asset_turn, 'amount': amount_turn})
            if asset not in emulated_balance_config['current'][exchange]:
                emulated_balance_config['current'][exchange][asset] = {
                    'available': 0,
                    'total': 0
                }
            emulated_balance_config['current'][exchange][asset]['available'] -= amount
            emulated_balance_config['current'][exchange][asset]['total'] -= amount
            if asset_turn not in emulated_balance_config['current'][exchange]:
                emulated_balance_config['current'][exchange][asset_turn] = {
                    'available': 0,
                    'total': 0
                }
            emulated_balance_config['current'][exchange][asset_turn]['available'] += amount_turn
            emulated_balance_config['current'][exchange][asset_turn]['total'] += amount_turn
        case 'order_create':
            emulated_balance['values'].append({'asset': asset, 'amount': -1 * amount})
            emulated_balance_config['current'][exchange][asset]['available'] -= amount
        case 'order_cancel':
            emulated_balance['values'].append({'asset': asset, 'amount': amount})
            emulated_balance_config['current'][exchange][asset]['available'] += amount
        case 'order_fill':
            emulated_balance['values'].append({'asset': asset, 'amount': -1 * amount})
            emulated_balance_config['current'][exchange][asset]['total'] -= amount
        case 'deposit': 
            emulated_balance['values'].append({'asset': asset, 'amount': amount})
            emulated_balance_config['current'][exchange][asset]['available'] += amount
            emulated_balance_config['current'][exchange][asset]['total'] += amount
        case 'withdrawal':
            emulated_balance['values'].append({'asset': asset, 'amount': -1 * amount})
            emulated_balance_config['current'][exchange][asset]['available'] -= amount
            emulated_balance_config['current'][exchange][asset]['total'] -= amount
            
    f = open( emulated_balance_file, 'w+', encoding='UTF-8')
    f.write( json.dumps(emulated_balance) )
    f.close()      
        
    f = open( emulated_balance_config_file, 'w+', encoding='UTF-8')
    f.write( json.dumps(emulated_balance_config) )
    f.close()  
    
    return Response('OK')


@api_view(['POST'])
@permission_classes([AllowAny])
def evaluate_trades(request):
    if not 'name' in request.data:
        return Response('request must has param name', status=status.HTTP_400_BAD_REQUEST)
    if not 'type' in request.data:
        return Response('request must has param type', status=status.HTTP_400_BAD_REQUEST)
    if not 'profit_asset' in request.data:
        return Response('request must has param profit_asset', status=status.HTTP_400_BAD_REQUEST)
    if not 'profit_extra' in request.data:
        return Response('request must has param profit_extra', status=status.HTTP_400_BAD_REQUEST)
    
    name = request.data['name']
    type = request.data['type']
    profit_asset = request.data['profit_asset']
    profit_extra = request.data['profit_extra']
    
    process = {
        'process': 'emulated_balance_evaluate_trades',
        'username': request.user.username,
        'params': {
            'emulated_balance_name': name, 
            'type': type,
            'profit_asset': profit_asset, 
            'profit_extra': profit_extra, 
        }
    }
        
    f = open( '../process_files/' + str(int(time.time() * 1e3)) + '.json', 'w+', encoding='UTF-8')
    f.write( json.dumps(process) )
    f.close()                    
    
    return Response('OK')

@api_view(['GET'])
@permission_classes([AllowAny])
def get_process_data(request):
    if not 'process' in request.GET:
        return Response('request must has param process', status=status.HTTP_400_BAD_REQUEST)
    
    process = request.GET.get("process")
    
    emulated_balances_processes_folder = '../process_files/data/emulated_balances/%s' % (process)
    if not os.path.isdir(emulated_balances_processes_folder):
        return Response('process does not exist', status=status.HTTP_400_BAD_REQUEST)
    emulated_balances_processes = []
    for process in os.listdir(emulated_balances_processes_folder):
        emulated_balance_process_file = emulated_balances_processes_folder + '/' + process
        emulated_balance_process = json.loads(open(emulated_balance_process_file, 'r', encoding='UTF-8').read())
        emulated_balance_process['name'] = process
        emulated_balances_processes.append(emulated_balance_process)
        
    return Response(emulated_balances_processes)