import json
import os
import time
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.response import Response
from ..utils import DATA_FOLDER, DATA_OLD_FOLDER
from damexCommons.tools.dbs import get_exchange_db

exchange_db = get_exchange_db(db_connection='exchange_connector')

ADDITIONAL_API_PARAMS = {'bitmart': ['memo'], 'kucoin': ['passphrase']}

#MM DASHBOARD - IMPLEMENTS
@api_view(['POST'])
@permission_classes([AllowAny])
def reset_pnl_accumulated(request):
    if not 'exchange' in request.data:
        return Response('request must has param exchange', status=status.HTTP_400_BAD_REQUEST)
    if not 'market' in request.data:
        return Response('request must has param market', status=status.HTTP_400_BAD_REQUEST)
    exchange = request.data['exchange']
    market = request.data['market']
    info_file_path = '%s/%s/%s/%s/%s' % (DATA_FOLDER, exchange, 'current_pnl', market, '/info.json')
    if os.path.exists(info_file_path):
        with open(info_file_path, "r", encoding='UTF-8') as jsonFile:
            info = json.load(jsonFile)
    else:
        info = {}
    info['reset'] = True
    if not 'reset_last_file_names' in info:
        info['reset_last_file_names'] = []
    info['reset_last_file_names'].append(info['last_file_name'])
    with open(info_file_path, "w", encoding='UTF-8') as jsonFile:
        json.dump(info, jsonFile)
    return Response('OK')

@api_view(['GET'])
@permission_classes([IsAdminUser])
def get_apis(request):
    apis_file = '../base/apis_new.json'
    apis = json.loads(open(apis_file, 'r', encoding='UTF-8').read())
    apis_reduced = []
    for api in apis:
        exchange = api.split('__')[0]
        name = api.split('__')[1]
        values = []
        for value in apis[api]:
            values.append({
                'timestamp': value['timestamp'],
                'api_key': value['api_key'][:4] + '...' + value['api_key'][-4:]
            })
        apis_reduced.append({'exchange': exchange, 'name': name, 'values': values})
    return Response(apis_reduced)

@api_view(['POST'])
@permission_classes([IsAdminUser])
def add_api(request):
    if not 'name' in request.data:
        return Response('request must has param name', status=status.HTTP_400_BAD_REQUEST) 
    if not 'exchange' in request.data:
        return Response('request must has param exchange', status=status.HTTP_400_BAD_REQUEST) 
    if not 'key' in request.data:
        return Response('request must has param key', status=status.HTTP_400_BAD_REQUEST)   
    if not 'secret' in request.data:
        return Response('request must has param secret', status=status.HTTP_400_BAD_REQUEST)  
    if not 'additionals' in request.data:
        return Response('request must has param additionals', status=status.HTTP_400_BAD_REQUEST)
    
    name = request.data['name']
    exchange = request.data['exchange']
    key = request.data['key']
    secret = request.data['secret']
    additionals = request.data['additionals']
        
    if exchange in ADDITIONAL_API_PARAMS:
        for additional_param in ADDITIONAL_API_PARAMS[exchange]:
            if not additional_param in additionals:
                return Response(f'request must has param {additional_param} in additionals for {exchange}', status=status.HTTP_400_BAD_REQUEST) 
                        
    apis_file = '../base/apis_new.json'
    apis = json.loads(open(apis_file, 'r', encoding='UTF-8').read())
    
    full_name = exchange + '__' + name
        
    value = {'timestamp': int(time.time() * 1e3), 'api_key': key, 'api_secret': secret}
    
    if not additionals is None:
        for key in additionals:
            value['api_' + key] = additionals[key]
    
    if not full_name in apis:        
        apis[full_name] = []
    
    apis[full_name].insert(0, value)
            
    f = open(apis_file, 'w+', encoding='UTF-8')
    f.write(json.dumps(apis))
    f.close()
    
    return Response('OK')

@api_view(['POST'])
@permission_classes([IsAdminUser])
def change_default_api(request):
    if not 'name' in request.data:
        return Response('request must has param name', status=status.HTTP_400_BAD_REQUEST) 
    if not 'exchange' in request.data:
        return Response('request must has param exchange', status=status.HTTP_400_BAD_REQUEST) 
    if not 'timestamp' in request.data:
        return Response('request must has param timestamp', status=status.HTTP_400_BAD_REQUEST)
        
    apis_file = '../base/apis_new.json'
    apis = json.loads(open(apis_file, 'r', encoding='UTF-8').read())
    
    name = request.data['name']
    exchange = request.data['exchange']
    timestamp = request.data['timestamp']
    
    full_name = exchange + '__' + name
    if full_name not in apis:
        return Response('api does not exist', status=status.HTTP_400_BAD_REQUEST)
        
    index_to_move = next((i for i, item in enumerate(apis[full_name]) if item['timestamp'] == timestamp), -1)
    if index_to_move == -1:
        return Response('timestamp does not exist', status=status.HTTP_400_BAD_REQUEST)
    
    api_to_move = apis[full_name].pop(index_to_move)
    apis[full_name].insert(0, api_to_move)

    f = open(apis_file, 'w+', encoding='UTF-8')
    f.write(json.dumps(apis))
    f.close()
    
    return Response('OK')
    
@api_view(['GET'])
@permission_classes([IsAdminUser])
def get_api_params(request):
    if not 'exchange' in request.GET:
        return Response('request must has param exchange', status=status.HTTP_400_BAD_REQUEST) 
    params = ['key', 'secret']
    exchange = request.GET.get('exchange')
    if exchange in ADDITIONAL_API_PARAMS:
        params.extend(ADDITIONAL_API_PARAMS[exchange])
    
    return Response(params)

@api_view(['GET'])
@permission_classes([IsAdminUser])
def get_wallets(request):
    wallets_file = '../base/wallets.json'
    wallets = json.loads(open(wallets_file, 'r', encoding='UTF-8').read())
    wallets_reduced = []
    for wallet in wallets:
        wallets_reduced.append(
            {
                'name': wallet, 
                'chain': wallets[wallet]['chain'], 
                'network': wallets[wallet]['network'], 
                'connectors': wallets[wallet]['connectors'],
                'address': wallets[wallet]['address']
            })
    return Response(wallets_reduced)
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_treasury_overview(request):
    
    treasury = {
        'fireblocks__apps': [], 
        'fireblocks__otc': [], 
        'mm__cex': [], 
        'mm__dex': [], 
        'others': []
    }
    
    for path_name in os.listdir('%s/%s/%s' % (DATA_FOLDER, 'fireblocks', 'current_values')):
        info_path = '%s/%s/%s/%s/%s' % (DATA_FOLDER, 'fireblocks', 'current_values', path_name, 'info.json')
        type = 'fireblocks__' + path_name.split('__')[0]
        info = json.loads(open(info_path, 'r', encoding='UTF-8').read())
        last_balance_file = '%s/%s/%s/%s/%s' % (DATA_FOLDER, 'fireblocks', 'current_values', path_name, info['last_file_name'])
        if not os.path.isfile(last_balance_file):
            last_balance_file = '%s/%s/%s/%s/%s' % (DATA_OLD_FOLDER, 'fireblocks', 'current_values', path_name, info['last_file_name'])
        last_balance = json.loads(open(last_balance_file, 'r', encoding='UTF-8').read())
        treasury[type].append(last_balance)
    
    mm_cex_exchanges = ['bitmart', 'mexc', 'coinstore', 'tidex', 'ascendex']
    for mm_cex_exchange in mm_cex_exchanges:
        info_path = '%s/%s/%s/%s/%s' % (DATA_FOLDER, 'fireblocks', 'current_values', 'NONE', 'info.json')
        info = json.loads(open(info_path, 'r', encoding='UTF-8').read())
        last_balance_file = '%s/%s/%s/%s/%s' % (DATA_FOLDER, 'fireblocks', 'current_values', 'NONE', info['last_file_name'])
        if not os.path.isfile(last_balance_file):
            last_balance_file = '%s/%s/%s/%s/%s' % (DATA_OLD_FOLDER, 'fireblocks', 'current_values', 'NONE', info['last_file_name'])
        last_balance = json.loads(open(last_balance_file, 'r', encoding='UTF-8').read())
        last_balance['name'] = mm_cex_exchange + ' mm'
        treasury['mm__cex'].append(last_balance)
        
    for path_name in os.listdir('%s/%s/%s' % (DATA_FOLDER, 'gateway', 'current_values')):
        info_path = '%s/%s/%s/%s/%s' % (DATA_FOLDER, 'gateway', 'current_values', path_name, 'info.json')
        info = json.loads(open(info_path, 'r', encoding='UTF-8').read())
        last_balance_file = '%s/%s/%s/%s/%s' % (DATA_FOLDER, 'gateway', 'current_values', path_name, info['last_file_name'])
        if not os.path.isfile(last_balance_file):
            last_balance_file = '%s/%s/%s/%s/%s' % (DATA_OLD_FOLDER, 'gateway', 'current_values', path_name, info['last_file_name'])
        last_balance = json.loads(open(last_balance_file, 'r', encoding='UTF-8').read())
        treasury['mm__dex'].append(last_balance)   
        
    return Response(treasury)
  