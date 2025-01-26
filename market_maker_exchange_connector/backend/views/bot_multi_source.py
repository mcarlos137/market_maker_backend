import json
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
import time
import os
from damexCommons.tools.bot import bot_exist, get_bot_group

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create(request):
    if not 'bot_id' in request.data:
        return Response('request must has param bot_id', status=status.HTTP_400_BAD_REQUEST)
    if not 'bot_type' in request.data:
        return Response('request must has param bot_type', status=status.HTTP_400_BAD_REQUEST)
    if not 'exchanges_apis' in request.data and not 'connectors_wallets' in request.data:
        return Response('request must has param exchanges_apis or connectors_wallets', status=status.HTTP_400_BAD_REQUEST)
    if not 'strategy' in request.data:
        return Response('request must has param strategy', status=status.HTTP_400_BAD_REQUEST)
    if not 'base_assets' in request.data:
        return Response('request must has base_assets', status=status.HTTP_400_BAD_REQUEST)
    if not 'quote_asset' in request.data:
        return Response('request must has param quote_asset', status=status.HTTP_400_BAD_REQUEST)
    if not 'region' in request.data:
        return Response('request must has param region', status=status.HTTP_400_BAD_REQUEST)
    if not 'use' in request.data:
        return Response('request must has param use', status=status.HTTP_400_BAD_REQUEST)
    if not 'tick_time' in request.data:
        return Response('request must has param tick_time', status=status.HTTP_400_BAD_REQUEST)
    if not 'emulated_balance' in request.data:
        return Response('request must has param emulated_balance', status=status.HTTP_400_BAD_REQUEST)
        
    exchanges_apis: dict = None
    if 'exchanges_apis' in request.data:
        exchanges_apis = json.loads(request.data['exchanges_apis'])
    connectors_wallets: dict = None
    if 'connectors_wallets' in request.data:
        connectors_wallets = json.loads(request.data['connectors_wallets'])
    if exchanges_apis is None and connectors_wallets is None:
        return Response('request must has values in exchanges_apis or connectors_wallets', status=status.HTTP_400_BAD_REQUEST)
            
    region: str = request.data['region']
    if not region in ['ireland', 'japan']:
        return Response('request param region must be ireland or japan', status=status.HTTP_400_BAD_REQUEST)
    
    emulated_balance_name = request.data['emulated_balance'] 
    emulated_balance_folder = '../base/emulated_balances/' + emulated_balance_name
    if not os.path.isdir(emulated_balance_folder):
        return Response('emulated_balance does not exist', status=status.HTTP_400_BAD_REQUEST)
    
    bot_id: str = request.data['bot_id']
    bot_type: str = request.data['bot_type']
    bot_group: str = get_bot_group(bot_type=bot_type)
    
    if bot_exist(bot_id=bot_id, bot_type=bot_type):
        return Response('bot already exists', status=status.HTTP_400_BAD_REQUEST)

    base_assets: list[str] = request.data['base_assets']
    if len(base_assets) == 0:
        return Response('request param base_assets must have values', status=status.HTTP_400_BAD_REQUEST)
    base_assets_str = ' '.join([str(elem) for elem in base_assets])   
    
    print('base_assets_str', base_assets_str) 
    
    strategy: str = request.data['strategy']
    quote_asset: str = request.data['quote_asset']
    use: str = request.data['use']
    tick_time: int = request.data['tick_time']
    
    testing: bool = False
    if 'testing' in request.data:
        testing = request.data['testing'] 
    
    action = {
        'action': 'create_bot_multi_source',
        'username': request.user.username,
        'params': {
            'bot_id': bot_id, 
            'bot_group': bot_group, 
            'bot_type': bot_type, 
            'exchanges_apis': json.dumps(exchanges_apis) if exchanges_apis is not None else None, 
            'connectors_wallets': json.dumps(connectors_wallets) if connectors_wallets is not None else None,
            'strategy': strategy, 
            'base_assets': base_assets_str,
            'quote_asset': quote_asset,
            'region': region,
            'tick_time': tick_time,
            'use': use,
            'testing': testing,
            'emulated_balance': emulated_balance_name,
            'creation_timestamp': int(time.time() * 1000)
        }
    }
        
    actions = [action]
    f = open( '../action_files/' + str(int(time.time() * 1e3)) + '.json', 'w+', encoding='UTF-8')
    f.write( json.dumps(actions) )
    f.close()                    
    return Response('OK')
