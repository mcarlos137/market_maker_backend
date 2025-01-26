import json
import os
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
import time
from damexCommons.tools.bot import STRATEGY_PARAMS, get_strategy_bots, add_new_attributes_values_to_bot_config

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def fetch_params(request):
    if not 'bot_type' in request.GET:
        return Response('request must has param bot_type', status=status.HTTP_400_BAD_REQUEST)
    bot_type = request.GET.get("bot_type")
    return Response(STRATEGY_PARAMS[bot_type])

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create(request):
    if not 'strategy_id' in request.data:
        return Response('request must has param strategy_id', status=status.HTTP_400_BAD_REQUEST) 
    if not 'strategy_type' in request.data:
        return Response('request must has param strategy_type', status=status.HTTP_400_BAD_REQUEST)   
    if not 'region' in request.data:
        return Response('request must has param region', status=status.HTTP_400_BAD_REQUEST)  
    if not 'use' in request.data:
        return Response('request must has param use', status=status.HTTP_400_BAD_REQUEST) 
     
    strategy_id = request.data['strategy_id']
    strategy_type = request.data['strategy_type']
    region = request.data['region']
    use = request.data['use']
    
    strategies_folder = '../strategy_files'
    for strategy_file in os.listdir(strategies_folder):
        if strategy_id in strategy_file:
            return Response('strategy already exist', status=status.HTTP_400_BAD_REQUEST)         
                    
    params = {}
    for param in STRATEGY_PARAMS[strategy_type]:
        param_name = param['name']
        param_type = param['type']
        if not param_name in request.data:
            return Response(f'request must has param {param_name}', status=status.HTTP_400_BAD_REQUEST)
        elif param_type == 'json':
            json_param_format = json.loads(param['format'])
            json_param_value = json.loads(request.data[param_name])
            for p_f in json_param_format:
                if not p_f in json_param_value:
                    return Response(f'request param {param_name} must be like {json_param_format}', status=status.HTTP_400_BAD_REQUEST)
                if json_param_format[p_f] == 'int':
                    json_param_value[p_f] = int(json_param_value[p_f])
                elif json_param_format[p_f] == 'float':
                    json_param_value[p_f] = float(json_param_value[p_f])
                elif json_param_format[p_f] == 'str':
                    json_param_value[p_f] = str(json_param_value[p_f])
                elif json_param_format[p_f] == 'bool':
                    json_param_value[p_f] = bool(json_param_value[p_f])
                params[param_name] = json_param_value
        else:
            if param_type == 'int':
                params[param_name] = int(request.data[param_name])
            elif param_type == 'float':
                params[param_name] = float(request.data[param_name])
            elif param_type == 'str':
                params[param_name] = str(request.data[param_name])
            elif param_type == 'bool':
                params[param_name] = bool(request.data[param_name])
            
    params['strategy_id'] = strategy_id
    params['strategy_type'] = strategy_type
    params['region'] = region
    params['use'] = use
    params['version'] = 1
                        
    actions = [{
        'action': 'create_strategy',
        'username': request.user.username,
        'params': params
    }]
            
    f = open( '../action_files/' + str(int(time.time() * 1e3)) + '.json', 'w+', encoding='UTF-8')
    f.write( json.dumps(actions) )
    f.close()
    return Response('OK')

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def edit(request):
    if not 'strategy_id' in request.data:
        return Response('request must has param strategy_id', status=status.HTTP_400_BAD_REQUEST) 
    if not 'strategy_type' in request.data:
        return Response('request must has param strategy_type', status=status.HTTP_400_BAD_REQUEST)   
    if not 'region' in request.data:
        return Response('request must has param region', status=status.HTTP_400_BAD_REQUEST)  
    if not 'version' in request.data:
        return Response('request must has param version', status=status.HTTP_400_BAD_REQUEST)  
    if not 'use' in request.data:
        return Response('request must has param use', status=status.HTTP_400_BAD_REQUEST)  
    if not 'new_attributes_values' in request.data:
        return Response('request must has param new_attributes_values', status=status.HTTP_400_BAD_REQUEST)
    
    strategy_id = request.data['strategy_id']
    strategy_type = request.data['strategy_type']
    region = request.data['region']
    version = int(request.data['version'])
    previous_version = int(request.data['version'])
    use = request.data['use']
    new_attributes_values = json.loads(request.data['new_attributes_values'])
    
    strategies_folder = '../strategy_files'
    if not os.path.exists(strategies_folder + '/' + strategy_id + '_v' + str(version) + '.json'):
        return Response('strategy or version does not exist', status=status.HTTP_400_BAD_REQUEST) 
    
    strategy = json.loads(open(strategies_folder + '/' + strategy_id + '_v' + str(version) + '.json', 'r', encoding='UTF-8').read())
    
    while True:
        if not os.path.exists(strategies_folder + '/' + strategy_id + '_v' + str(version) + '.json'):
            break
        version += 1
                    
    params = {}
    for param in STRATEGY_PARAMS[strategy_type]:
        param_name = param['name']
        param_type = param['type']
        if not param_name in new_attributes_values:
            params[param_name] = strategy[param_name]
        elif param_type == 'json':
            json_param_format = json.loads(param['format'])
            json_param_value = new_attributes_values[param_name]
            for p_f in json_param_format:
                if not p_f in json_param_value:
                    return Response(f'request param {param_name} must be like {json_param_format}', status=status.HTTP_400_BAD_REQUEST)
                if json_param_format[p_f] == 'int':
                    json_param_value[p_f] = int(json_param_value[p_f])
                elif json_param_format[p_f] == 'float':
                    json_param_value[p_f] = float(json_param_value[p_f])
                elif json_param_format[p_f] == 'str':
                    json_param_value[p_f] = str(json_param_value[p_f])
                elif json_param_format[p_f] == 'bool':
                    json_param_value[p_f] = bool(json_param_value[p_f])
                params[param_name] = json_param_value
        else:
            if param_type == 'int':
                params[param_name] = int(new_attributes_values[param_name])
            elif param_type == 'float':
                params[param_name] = float(new_attributes_values[param_name])
            elif param_type == 'str':
                params[param_name] = str(new_attributes_values[param_name])
            elif param_type == 'bool':
                params[param_name] = bool(new_attributes_values[param_name])
            
    params['strategy_id'] = strategy_id
    params['strategy_type'] = strategy_type
    params['region'] = region
    params['version'] = version
    params['use'] = use
                        
    actions = [{
        'action': 'create_strategy',
        'username': request.user.username,
        'params': params
    }]
    
    bots_to_update = get_strategy_bots(strategy_id=str(strategy_id + '_v' + str(previous_version)), strategy_type=strategy_type)
    for bot_to_update in bots_to_update:
        bot_config = add_new_attributes_values_to_bot_config(bot_id=bot_to_update['bot_id'], bot_type=bot_to_update['bot_type'], new_attributes_values={'strategy': strategy_id + '_v' + str(version)})
        actions.append(
            {
                'action': 'edit_bot',
                'username': request.user.username,
                'params': bot_config
            }
        )
        actions.append(
            {
                'action': 'restart_bot',
                'username': request.user.username,
                'params': {
                    'bot_id': bot_to_update['bot_id'], 
                    'bot_type': bot_to_update['bot_type'], 
                    'region': bot_to_update['region']
                }
            }
        )
        
    f = open( '../action_files/' + str(int(time.time() * 1e3)) + '.json', 'w+', encoding='UTF-8')
    f.write( json.dumps(actions) )
    f.close()
    return Response('OK')

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def fetch(request):
    if not 'strategy_type' in request.GET:
        return Response('request must has param strategy_type', status=status.HTTP_400_BAD_REQUEST)
    strategy_type = request.GET.get("strategy_type")
    strategy_id = None
    if 'strategy_id' in request.GET:
        strategy_id = request.GET.get("strategy_id")
    use = None
    if request.GET.get("use") is not None:
        use = request.GET.get("use")
    strategies = []
    strategies_folder = '../strategy_files'
    for strategy_file in os.listdir(strategies_folder):
        if not '.json' in strategy_file:
            continue
        if os.path.exists(strategies_folder + '/' + strategy_file):
            strategy = json.loads(open(strategies_folder + '/' + strategy_file, 'r', encoding='UTF-8').read())
            if use is not None and 'use' in strategy and strategy['use'] != use:
                continue
            if 'strategy_type' in strategy and strategy['strategy_type'] == strategy_type:
                if strategy_id is not None:
                    if str(strategy_id) == str(strategy_file.replace('.json', '')):
                        strategy['bots'] = get_strategy_bots(strategy_id=str(strategy_file.replace('.json', '')), strategy_type=strategy_type)
                        strategies.append(strategy)
                else:
                    strategy['bots'] = get_strategy_bots(strategy_id=str(strategy_file.replace('.json', '')), strategy_type=strategy_type)
                    strategies.append(strategy)
                                    
    return Response(strategies)