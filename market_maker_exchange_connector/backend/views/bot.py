import json
import os
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
import time
import asyncio
from damexCommons.tools.dbs import get_exchange_db
from damexCommons.tools.bot import bot_exist, get_bot_group, str_to_bool, get_bot_strategy

exchange_db = get_exchange_db(db_connection='exchange_connector')

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create(request):
    if not 'bot_id' in request.data:
        return Response('request must has param bot_id', status=status.HTTP_400_BAD_REQUEST)
    if not 'bot_type' in request.data:
        return Response('request must has param bot_type', status=status.HTTP_400_BAD_REQUEST)
    if not 'exchange' in request.data and not 'connector' in request.data:
        return Response('request must has param exchange or connector', status=status.HTTP_400_BAD_REQUEST)
    if not 'api' in request.data and not 'wallet' in request.data:
        return Response('request must has param api or wallet', status=status.HTTP_400_BAD_REQUEST)
    if not 'strategy' in request.data:
        return Response('request must has param strategy', status=status.HTTP_400_BAD_REQUEST)
    if not 'base_asset' in request.data:
        return Response('request must has param base_asset', status=status.HTTP_400_BAD_REQUEST)
    if not 'quote_asset' in request.data:
        return Response('request must has param quote_asset', status=status.HTTP_400_BAD_REQUEST)
    if not 'region' in request.data:
        return Response('request must has param region', status=status.HTTP_400_BAD_REQUEST)
    if not 'tick_time' in request.data:
        return Response('request must has param tick_time', status=status.HTTP_400_BAD_REQUEST)
    
    use = 'mm'
    if 'use' in request.data:
        use: str = request.data['use'] 
    
    region = request.data['region']
    
    if not region in ['ireland', 'japan']:
         return Response('request param region must be ireland or japan', status=status.HTTP_400_BAD_REQUEST)
    
    bot_id = request.data['bot_id']
    bot_type = request.data['bot_type']
    bot_group = get_bot_group(bot_type=bot_type)
    
    if bot_exist(bot_id=bot_id, bot_type=bot_type):
        return Response('bot already exists', status=status.HTTP_400_BAD_REQUEST)
    
    exchange = None
    connector = None
    api = None
    wallet = None
    if 'exchange' in request.data:
        exchange = request.data['exchange']
    if 'connector' in request.data:
        connector = request.data['connector']
    if 'api' in request.data:
        api = request.data['api']
    if 'wallet' in request.data:
        wallet = request.data['wallet']
        
    strategy = request.data['strategy']
    base_asset = request.data['base_asset']
    quote_asset = request.data['quote_asset']
    tick_time = request.data['tick_time']
    action = {
        'action': 'create_bot',
        'username': request.user.username,
        'params': {
            'bot_id': bot_id, 
            'bot_group': bot_group, 
            'bot_type': bot_type, 
            'exchange': exchange, 
            'api': api, 
            'connector': connector,
            'wallet': wallet,
            'strategy': strategy, 
            'base_asset': base_asset,
            'quote_asset': quote_asset,
            'region': region,
            'tick_time': tick_time,
            'use': use,
            'creation_timestamp': int(time.time() * 1000)
        }
    }
        
    actions = [action]
    f = open( '../action_files/' + str(int(time.time() * 1e3)) + '.json', 'w+', encoding='UTF-8')
    f.write( json.dumps(actions) )
    f.close()                    
    return Response('OK')

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def execute_action(request):
    if not 'bot_id' in request.data:
        return Response('request must has param bot_id', status=status.HTTP_400_BAD_REQUEST)
    if not 'bot_type' in request.data:
        return Response('request must has param bot_type', status=status.HTTP_400_BAD_REQUEST)
    if not 'region' in request.data:
        return Response('request must has param region', status=status.HTTP_400_BAD_REQUEST)
    if not 'action' in request.data:
        return Response('request must has param action', status=status.HTTP_400_BAD_REQUEST)
    
    region = request.data['region']
    
    if not region in ['ireland', 'japan']:
         return Response('request param region must be ireland or japan', status=status.HTTP_400_BAD_REQUEST)
    
    action = request.data['action']
    
    if not action in ['restart', 'activate', 'inactivate']:
         return Response('request param action must be restart, activate or inactivate', status=status.HTTP_400_BAD_REQUEST)
    
    bot_id = request.data['bot_id']
    bot_type = request.data['bot_type']
    bot_group = get_bot_group(bot_type=bot_type)
    
    if not bot_exist(bot_id=bot_id, bot_type=bot_type, region=region):
        return Response('bot does not exist in the region', status=status.HTTP_400_BAD_REQUEST)
    
    actions = [{
        'action': action + '_bot',
        'username': request.user.username,
        'params': {
            'bot_id': bot_id, 
            'bot_group': bot_group, 
            'bot_type': bot_type, 
            'region': region
        }
    }]
    f = open( '../action_files/' + str(int(time.time() * 1e3)) + '.json', 'w+', encoding='UTF-8')
    f.write( json.dumps(actions) )
    f.close()                    
    return Response('OK')

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_status(request):
    if not 'bot_id' in request.GET:
        return Response('request must has param bot_id', status=status.HTTP_400_BAD_REQUEST)
    if not 'bot_type' in request.GET:
        return Response('request must has param bot_type', status=status.HTTP_400_BAD_REQUEST)
    bot_id = request.GET.get("bot_id")
    bot_type = request.GET.get("bot_type")
    bot_group = get_bot_group(bot_type=bot_type)
    bot_folder = '../' + bot_group + '_bots/' + bot_id
    if os.path.exists(bot_folder) and os.path.isdir(bot_folder):
        bot_config_file = bot_folder + '/config.json'
        if os.path.exists(bot_config_file):
            config = json.loads(open(bot_config_file, 'r', encoding='UTF-8').read())
            if config['active']:
                return Response('ACTIVE')
            else:
                return Response('INACTIVE')
        else: 
            return Response('CREATING')
    else:
        return Response('DOES NOT EXIST')
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def fetch(request):
    
    bot_type = None
    if request.GET.get("bot_type") is not None:
        bot_type = request.GET.get("bot_type")
    use = None
    if request.GET.get("use") is not None:
        use = request.GET.get("use")
    bot_id = None
    if request.GET.get("bot_id") is not None:
        bot_id = request.GET.get("bot_id")
    bots = []
    bot_groups = ['maker', 'taker', 'vol', 'arbitrage']
    if bot_type is not None:
        bot_groups = [get_bot_group(bot_type=bot_type)]
        
    for bot_group in bot_groups:
        bots_folder = '../' + bot_group + '_bots'
        for bot_file in os.listdir(bots_folder):
            if os.path.exists(bots_folder + '/' + bot_file + '/config.json'):
                bot = json.loads(open(bots_folder + '/' + bot_file + '/config.json', 'r', encoding='UTF-8').read())
                if use is not None and 'use' in bot and bot['use'] != use:
                    continue
                if bot_type is not None and bot['bot_type'] != bot_type:
                    continue
                if bot_id is not None and str(bot_id) != str(bot_file):
                    continue
                bots.append(json.loads(open(bots_folder + '/' + bot_file + '/config.json', 'r', encoding='UTF-8').read()))

    return Response(bots)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def edit(request):
    if not 'bot_id' in request.data:
        return Response('request must has param bot_id', status=status.HTTP_400_BAD_REQUEST)
    if not 'bot_type' in request.data:
        return Response('request must has param bot_type', status=status.HTTP_400_BAD_REQUEST)
    if not 'region' in request.data:
        return Response('request must has param region', status=status.HTTP_400_BAD_REQUEST)
    if not 'new_attributes_values' in request.data:
        return Response('request must has param new_attributes_values', status=status.HTTP_400_BAD_REQUEST)
    
    bot_id = request.data['bot_id']
    bot_type = request.data['bot_type']
    region = request.data['region']
    new_attributes_values = json.loads(request.data['new_attributes_values'])
    
    if not bot_exist(bot_id=bot_id, bot_type=bot_type, region=region):
        return Response('bot does not exist in the region', status=status.HTTP_400_BAD_REQUEST)
    
    new_attributes_values['bot_id'] = bot_id
    new_attributes_values['bot_type'] = bot_type
    new_attributes_values['bot_group'] = get_bot_group(bot_type=bot_type)
    new_attributes_values['region'] = region
    
    actions = [{
        'action': 'edit_bot',
        'username': request.user.username,
        'params': new_attributes_values
    }]
    f = open( '../action_files/' + str(int(time.time() * 1e3)) + '.json', 'w+', encoding='UTF-8')
    f.write( json.dumps(actions) )
    f.close()                    
    return Response('OK')
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_volume(request):
    if not 'bot_types' in request.GET:
        return Response('request must has param bot_types', status=status.HTTP_400_BAD_REQUEST)
    if not 'turnover' in request.GET:
        return Response('request must has param turnover', status=status.HTTP_400_BAD_REQUEST)

    bot_types: list = request.GET.get("bot_types").split(',')
    turnover: bool = str_to_bool(request.GET.get('turnover'))
    
    market: str = 'DAMEX-USDT'
    if 'market' in request.GET:
        market = request.GET.get('market')
    
    exchanges: list = ['ascendex', 'bitmart', 'coinstore', 'mexc', 'tidex']
    if 'exchanges' in request.GET:
        exchanges = request.GET.get("exchanges").split(',')
    
    initial_timestamp = 0
    final_timestamp = 99999999999999999

    if request.GET.get('initial_timestamp') is not None:
        initial_timestamp = int(request.GET.get('initial_timestamp'))
    if request.GET.get('final_timestamp') is not None:
        final_timestamp = int(request.GET.get('final_timestamp'))

    bots_volume_buy = asyncio.run(exchange_db.get_trades_volume_db(
        exchanges=exchanges,
        base_asset=market.split('-')[0],
        quote_asset=market.split('-')[1],
        sides=[1],
        bot_types=bot_types,
        initial_timestamp=initial_timestamp,
        final_timestamp=final_timestamp,
        turnover=turnover        
        )
    )
    bots_volume_sell = asyncio.run(exchange_db.get_trades_volume_db(
        exchanges=exchanges,
        base_asset=market.split('-')[0],
        quote_asset=market.split('-')[1],
        sides=[2],
        bot_types=bot_types,
        initial_timestamp=initial_timestamp,
        final_timestamp=final_timestamp,
        turnover=turnover        
        )
    )
    bots_volume = {
        'BUY': bots_volume_buy,
        'SELL': bots_volume_sell,
        'DIFF': bots_volume_buy - bots_volume_sell
    }    
    return Response(bots_volume)

    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_trades(request):
    if not 'bot_types' in request.GET:
        return Response('request must has param bot_types', status=status.HTTP_400_BAD_REQUEST)
    if not 'sides' in request.GET:
        return Response('request must has param sides', status=status.HTTP_400_BAD_REQUEST)
    if not 'exchanges' in request.GET:
        return Response('request must has param exchanges', status=status.HTTP_400_BAD_REQUEST)
    if not 'offset' in request.GET:
        return Response('request must has param offset', status=status.HTTP_400_BAD_REQUEST)
    if not 'final_timestamp' in request.GET:
        return Response('request must has param final_timestamp', status=status.HTTP_400_BAD_REQUEST)

    bot_types: list = request.GET.get("bot_types").split(',')
    sides: list = request.GET.get("sides").split(',')
    exchanges: list = request.GET.get("exchanges").split(',')
    offset: int = request.GET.get("offset")
    final_timestamp: int = request.GET.get("final_timestamp")
    
    market = 'DAMEX-USDT' if not 'market' in request.GET else request.GET.get("market")
    
    return Response(asyncio.run(
        exchange_db.fetch_trades_db(
            exchanges=exchanges, 
            base_asset=market.split('-')[0], 
            quote_asset=market.split('-')[1], 
            sides=[1, 2], 
            order_timestamp='DESC', 
            final_timestamp=final_timestamp, 
            offset=offset, 
            bot_types=bot_types
            )
    )) 
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def fetch_trades(request):
    if not 'bot_type' in request.GET:
        return Response('request must has param bot_type', status=status.HTTP_400_BAD_REQUEST)
    if not 'bot_id' in request.GET:
        return Response('request must has param bot_id', status=status.HTTP_400_BAD_REQUEST)
    if not 'final_timestamp' in request.GET:
        return Response('request must has param final_timestamp', status=status.HTTP_400_BAD_REQUEST)
    if not 'offset' in request.GET:
        return Response('request must has param offset', status=status.HTTP_400_BAD_REQUEST)

    bot_type: str = request.GET.get("bot_type")
    bot_id: str = request.GET.get("bot_id")
    final_timestamp: int = request.GET.get("final_timestamp")
    offset: int = request.GET.get("offset")
    
    return Response(asyncio.run(
        exchange_db.fetch_trades_by_bot_db(
            bot_type=bot_type,
            bot_id=bot_id,
            order_timestamp='DESC', 
            final_timestamp=final_timestamp, 
            offset=offset, 
            )
    )) 
              

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_strategy(request):
    if not 'bot_type' in request.GET:
        return Response('request must has param bot_type', status=status.HTTP_400_BAD_REQUEST)
    if not 'bot_id' in request.GET:
        return Response('request must has param bot_id', status=status.HTTP_400_BAD_REQUEST)
    bot_type: str = request.GET.get("bot_type")
    bot_id: str = request.GET.get("bot_id")
    if not bot_exist(bot_id=bot_id, bot_type=bot_type):
        return Response('bot does not exist', status=status.HTTP_400_BAD_REQUEST)    
    return Response(get_bot_strategy(bot_id=bot_id, bot_type=bot_type))