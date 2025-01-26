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
    emulated_balance_init_file = emulated_balances_folder + '/' + name + '/init.json'
    
    emulated_balance_init = None
    if not os.path.isdir(emulated_balance_folder):
        os.makedirs(emulated_balance_folder)
        os.makedirs(emulated_balance_folder + '/orders')
        os.makedirs(emulated_balance_folder + '/trades')
        os.makedirs(emulated_balance_folder + '/deposits')
        os.makedirs(emulated_balance_folder + '/withdrawals')
        emulated_balance_init = {
            'name': name, 
            'exchanges': {
                exchange: {
                    asset: {
                        'available': amount,
                        'total': amount
                    }
                }
            }
        }
    else:
        emulated_balance_init = json.loads(open(emulated_balance_init_file, 'r', encoding='UTF-8').read())
        if exchange not in emulated_balance_init['exchanges']:
             emulated_balance_init['exchanges'][exchange] = {}
        emulated_balance_init['exchanges'][exchange][asset] = {'available': amount, 'total': amount}
    
    if emulated_balance_init is None:
        return Response('FAILED')
    
    f = open( emulated_balance_init_file, 'w+', encoding='UTF-8')
    f.write( json.dumps(emulated_balance_init) )
    f.close()                    
    return Response('OK')


@api_view(['GET'])
@permission_classes([AllowAny])
def fetch(request):
    name = None
    type = 'current'
    if 'name' in request.GET:
        name = request.GET.get("name")
    if 'type' in request.GET:
        type = request.GET.get("type")
    emulated_balances = []
    emulated_balances_folder = '../base/emulated_balances'
    if name is not None:
        emulated_balance_init_file = emulated_balances_folder + '/' + name + '/init.json'
        if not os.path.exists(emulated_balance_init_file):
            return Response(emulated_balances)   
        if type == 'initial':
            emulated_balances.append(json.loads(open(emulated_balance_init_file, 'r', encoding='UTF-8').read()))
        elif type == 'current':
            emulated_balances.append(fetch_current_balance(name=name))
    else:
        for name in os.listdir(emulated_balances_folder):
            emulated_balance_folder = emulated_balances_folder + '/' + name
            if not os.path.isdir(emulated_balance_folder):
                continue
            emulated_balance_init_file = emulated_balance_folder + '/init.json'
            if type == 'initial':
                emulated_balances.append(json.loads(open(emulated_balance_init_file, 'r', encoding='UTF-8').read()))
            elif type == 'current':
                emulated_balances.append(fetch_current_balance(name=name))
    for emulated_balance in emulated_balances:
        emulated_balances_total = {}
        for exchange in emulated_balance['exchanges']:
            for asset in emulated_balance['exchanges'][exchange]:
                if asset not in emulated_balances_total:
                    emulated_balances_total[asset] = {'available': 0, 'total': 0}
                emulated_balances_total[asset]['available'] += emulated_balance['exchanges'][exchange][asset]['available']
                emulated_balances_total[asset]['total'] += emulated_balance['exchanges'][exchange][asset]['total']
        emulated_balance['exchanges']['total'] = emulated_balances_total
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
        case 'order_create':
            emulated_balance['values'].append({'asset': asset, 'amount': -1 * amount})
        case 'order_cancel':
            emulated_balance['values'].append({'asset': asset, 'amount': amount})
        case 'order_fill':
            emulated_balance['values'].append({'asset': asset, 'amount': -1 * amount})
        case 'deposit': 
            emulated_balance['values'].append({'asset': asset, 'amount': amount})
        case 'withdrawal':
            emulated_balance['values'].append({'asset': asset, 'amount': -1 * amount})
        
    f = open( emulated_balance_file, 'w+', encoding='UTF-8')
    f.write( json.dumps(emulated_balance) )
    f.close()      
    return Response('OK')


def fetch_current_balance(name: str):
    emulated_balances_folder = '../base/emulated_balances'
    emulated_balance_folder = emulated_balances_folder + '/' + name
    emulated_balance_init_file = emulated_balance_folder + '/init.json'
    emulated_balance_init = json.loads(open(emulated_balance_init_file, 'r', encoding='UTF-8').read())
    for emulated_balance_folder_name in ['orders', 'trades', 'deposits', 'withdrawals']:
        emulated_balance_folder_by_type = emulated_balance_folder + '/' + emulated_balance_folder_name
        for emulated_balance_file in os.listdir(emulated_balance_folder_by_type):
            if os.path.isdir(emulated_balance_folder_by_type + '/' + emulated_balance_file):
                continue
            emulated_balance = json.loads(open(emulated_balance_folder_by_type + '/' + emulated_balance_file, 'r', encoding='UTF-8').read())
            exchange = emulated_balance['exchange']
            operation = emulated_balance['operation']
            values = emulated_balance['values']
            if exchange not in emulated_balance_init['exchanges']:
                emulated_balance_init['exchanges'][exchange] = {}
            for value in values:
                asset = value['asset']
                amount = value['amount']
                if asset not in emulated_balance_init['exchanges'][exchange]:
                    emulated_balance_init['exchanges'][exchange][asset] = {'available': 0, 'total': 0}
                match operation:
                    case 'order_create' | 'order_cancel':
                        emulated_balance_init['exchanges'][exchange][asset]['available'] += amount
                    case 'order_fill':
                        emulated_balance_init['exchanges'][exchange][asset]['total'] += amount
                    case 'deposit' | 'trade' | 'withdrawal':
                        emulated_balance_init['exchanges'][exchange][asset]['available'] += amount
                        emulated_balance_init['exchanges'][exchange][asset]['total'] += amount
    return emulated_balance_init
            