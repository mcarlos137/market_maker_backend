import json
import time
import os
import copy
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create(request):
    if not 'orchestration_rule_id' in request.data:
        return Response('request must has param orchestration_rule_id', status=status.HTTP_400_BAD_REQUEST)
    if not 'strategy' in request.data:
        return Response('request must has param strategy', status=status.HTTP_400_BAD_REQUEST)
    if not 'start_time' in request.data:
        return Response('request must has param start_time', status=status.HTTP_400_BAD_REQUEST)
    if not 'exchanges_apis' in request.data:
        return Response('request must has param exchanges_apis', status=status.HTTP_400_BAD_REQUEST)
    if not 'members' in request.data:
        return Response('request must has param members', status=status.HTTP_400_BAD_REQUEST)
    if not 'tick_time' in request.data:
        return Response('request must has param tick_time', status=status.HTTP_400_BAD_REQUEST)
    use = 'trading'
    if 'use' in request.data:
        use: str = request.data['use'] 
        
    region = 'ireland'
    orchestration_rule_id = request.data['orchestration_rule_id']
    
    if orchestration_rule_exist(orchestration_rule_id=orchestration_rule_id):
        return Response('orchestration rule already exists', status=status.HTTP_400_BAD_REQUEST)
    
    excluded_days: list[str] = []
    if 'excluded_days' in request.data:
        excluded_days = request.data['excluded_days']
    excluded_days_str = ' '.join([str(elem) for elem in excluded_days])
            
    strategy: str = request.data['strategy']
    start_time: str = request.data['start_time']
    exchanges_apis: dict = json.loads(request.data['exchanges_apis'])
    members: list[str] = request.data['members']
    tick_time: int = request.data['tick_time']
    members_str = ' '.join([str(elem) for elem in members])
    
    action = {
        'action': 'create_orchestration_rule',
        'username': request.user.username,
        'params': {
            'orchestration_rule_id': orchestration_rule_id, 
            'strategy': strategy, 
            'start_time': start_time,
            'exchanges_apis': json.dumps(exchanges_apis),
            'members': members_str,
            'region': region,
            'tick_time': tick_time,
            'excluded_days': excluded_days_str,
            'use': use,
            'creation_timestamp': int(time.time() * 1000),
            'target': {},
            'rules': []
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
    if not 'orchestration_rule_id' in request.data:
        return Response('request must has param orchestration_rule_id', status=status.HTTP_400_BAD_REQUEST)
    if not 'action' in request.data:
        return Response('request must has param action', status=status.HTTP_400_BAD_REQUEST)
    
    action = request.data['action']
    if not action in ['restart', 'activate', 'inactivate']:
         return Response('request param action must be restart, activate or inactivate', status=status.HTTP_400_BAD_REQUEST)
    
    orchestration_rule_id = request.data['orchestration_rule_id']
    region = 'ireland'
        
    if not orchestration_rule_exist(orchestration_rule_id=orchestration_rule_id):
        return Response('orchestration rule does not exist', status=status.HTTP_400_BAD_REQUEST)
    
    if action == 'activate':
        orchestration_rule_rules_file = '../orchestration_rules/' + orchestration_rule_id + '/rules.json'
        orchestration_rule_rules = json.loads(open(orchestration_rule_rules_file, 'r', encoding='UTF-8').read())
        orchestration_rule_target_file = '../orchestration_rules/' + orchestration_rule_id + '/target.json'
        orchestration_rule_target = json.loads(open(orchestration_rule_target_file, 'r', encoding='UTF-8').read())
        if len(orchestration_rule_rules) == 0:
            return Response('orchestration rule can not be activated because It does not have rules', status=status.HTTP_400_BAD_REQUEST)
        if len(orchestration_rule_target) == 0:
            return Response('orchestration rule can not be activated because It does not have a target', status=status.HTTP_400_BAD_REQUEST)
        
    actions = [{
        'action': action + '_orchestration_rule',
        'username': request.user.username,
        'params': {
            'orchestration_rule_id': orchestration_rule_id, 
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
    if not 'orchestration_rule_id' in request.GET:
        return Response('request must has param orchestration_rule_id', status=status.HTTP_400_BAD_REQUEST)
    orchestration_rule_id = request.GET.get("orchestration_rule_id")
    orchestration_rule_folder = '../orchestration_rules/' + orchestration_rule_id
    if os.path.exists(orchestration_rule_folder) and os.path.isdir(orchestration_rule_folder):
        orchestration_rule_config_file = orchestration_rule_folder + '/config.json'
        if os.path.exists(orchestration_rule_config_file):
            config = json.loads(open(orchestration_rule_config_file, 'r', encoding='UTF-8').read())
            if config['active']:
                return Response('ACTIVE')
            else:
                return Response('INACTIVE')
        else: 
            return Response('CREATING')
    else:
        return Response('DOES NOT EXIST')

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def edit(request):
    if not 'orchestration_rule_id' in request.data:
        return Response('request must has param orchestration_rule_id', status=status.HTTP_400_BAD_REQUEST)
    if not 'use' in request.data:
        return Response('request must has param use', status=status.HTTP_400_BAD_REQUEST)
    if not 'new_attributes_values' in request.data:
        return Response('request must has param new_attributes_values', status=status.HTTP_400_BAD_REQUEST)
    
    orchestration_rule_id = request.data['orchestration_rule_id']
    new_attributes_values = json.loads(request.data['new_attributes_values'])
    
    if not orchestration_rule_exist(orchestration_rule_id=orchestration_rule_id):
        return Response('orchestration rule does not exist', status=status.HTTP_400_BAD_REQUEST)
    
    new_attributes_values['orchestration_rule_id'] = orchestration_rule_id
    new_attributes_values['region'] = 'ireland'
    new_attributes_values['use'] = request.data['use']
    
    actions = [{
        'action': 'edit_orchestration_rule',
        'username': request.user.username,
        'params': new_attributes_values
    }]
    f = open( '../action_files/' + str(int(time.time() * 1e3)) + '.json', 'w+', encoding='UTF-8')
    f.write( json.dumps(actions) )
    f.close()                    
    return Response('OK')
    
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def edit_target(request):
    if not 'orchestration_rule_id' in request.data:
        return Response('request must has param orchestration_rule_id', status=status.HTTP_400_BAD_REQUEST)
    if not 'strategy' in request.data:
        return Response('request must has param strategy', status=status.HTTP_400_BAD_REQUEST)
    if not 'new_attributes_values' in request.data:
        return Response('request must has param new_attributes_values', status=status.HTTP_400_BAD_REQUEST)
                
    orchestration_rule_id = request.data['orchestration_rule_id']
    strategy = request.data['strategy']  
    new_attributes_values = json.loads(request.data['new_attributes_values'])
        
    if not orchestration_rule_exist(orchestration_rule_id=orchestration_rule_id):
        return Response('orchestration rule does not exist', status=status.HTTP_400_BAD_REQUEST)
            
    params = {
        'orchestration_rule_id': orchestration_rule_id,
        'region': 'ireland',
    }
    
    orchestration_rules_file = '../base/orchestration_rules.json'
    orchestration_rules = json.loads(open(orchestration_rules_file, 'r', encoding='UTF-8').read())
        
    try:
        params = add_attributes_values_to_params(target_strategy_params=orchestration_rules['target_strategy_params'][strategy], params=params, attributes_values=new_attributes_values) 
    except ValueError as e:
        return Response(e, status=status.HTTP_400_BAD_REQUEST)
        
    actions = [{
        'action': 'edit_orchestration_rule_target',
        'username': request.user.username,
        'params': params
    }]
        
    f = open( '../action_files/' + str(int(time.time() * 1e3)) + '.json', 'w+', encoding='UTF-8')
    f.write( json.dumps(actions) )
    f.close()                    
    return Response('OK')

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_rule(request):
    if not 'orchestration_rule_id' in request.data:
        return Response('request must has param orchestration_rule_id', status=status.HTTP_400_BAD_REQUEST)
    if not 'type' in request.data:
        return Response('request must has param type', status=status.HTTP_400_BAD_REQUEST)
    if not 'value' in request.data:
        return Response('request must has param value', status=status.HTTP_400_BAD_REQUEST)
    if not 'actions' in request.data:
        return Response('request must has param actions', status=status.HTTP_400_BAD_REQUEST)
    if not 'member' in request.data:
        return Response('request must has param member', status=status.HTTP_400_BAD_REQUEST)
    if not 'apply_on_target_completed' in request.data:
        return Response('request must has param apply_on_target_completed', status=status.HTTP_400_BAD_REQUEST)
    if not 'idle' in request.data:
        return Response('request must has param idle', status=status.HTTP_400_BAD_REQUEST)
    
    orchestration_rule_id = request.data['orchestration_rule_id']
    type = request.data['type']
    value = request.data['value']
    actions = json.loads(request.data['actions'])
    member = request.data['member']
    apply_on_target_completed = bool(request.data['apply_on_target_completed'])
    idle = bool(request.data['idle'])
        
    if not orchestration_rule_exist(orchestration_rule_id=orchestration_rule_id):
        return Response('orchestration rule does not exist', status=status.HTTP_400_BAD_REQUEST)
    
    orchestration_rule_rules_file = '../orchestration_rules/' + orchestration_rule_id + '/rules.json'
    orchestration_rule_rules: list = json.loads(open(orchestration_rule_rules_file, 'r', encoding='UTF-8').read())        
    
    last_id = 0
    if len(orchestration_rule_rules) > 0:
        last_id = orchestration_rule_rules[len(orchestration_rule_rules) - 1]['id']
            
    orchestration_rule_rules.append({
        'id': int(last_id) + 1,
        'type': type,
        'value': value,
        'actions': actions,
        'member': member,
        'apply_on_target_completed': apply_on_target_completed,
        'idle': idle
    })
        
    orchestration_rule_rules.sort(key=lambda x: int(x['id']))
        
    params = {
        'orchestration_rule_id': orchestration_rule_id,
        'region': 'ireland',
        'rules': orchestration_rule_rules
    }
                    
    actions = [{
        'action': 'edit_orchestration_rule_rules',
        'username': request.user.username,
        'params': params
    }]
            
    f = open( '../action_files/' + str(int(time.time() * 1e3)) + '.json', 'w+', encoding='UTF-8')
    f.write( json.dumps(actions) )
    f.close()                    
    return Response('OK')
    

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def remove_rule(request):
    if not 'orchestration_rule_id' in request.data:
        return Response('request must has param orchestration_rule_id', status=status.HTTP_400_BAD_REQUEST)
    if not 'id' in request.data:
        return Response('request must has param id', status=status.HTTP_400_BAD_REQUEST)
                
    orchestration_rule_id = request.data['orchestration_rule_id']
    id = request.data['id']  
        
    if not orchestration_rule_exist(orchestration_rule_id=orchestration_rule_id):
        return Response('orchestration rule does not exist', status=status.HTTP_400_BAD_REQUEST)
    
    orchestration_rule_rules_file = '../orchestration_rules/' + orchestration_rule_id + '/rules.json'
    orchestration_rule_rules = json.loads(open(orchestration_rule_rules_file, 'r', encoding='UTF-8').read())

    orchestration_rule_rules = [rule for rule in orchestration_rule_rules if str(rule['id']) != str(id)]
    orchestration_rule_rules_new = []

    for rule in orchestration_rule_rules[:]:
        new_rule = copy.deepcopy(rule)
        new_rule['actions'] = []
        if int(rule['id']) > int(id):
            new_rule['id'] = str(int(rule['id']) - 1)
        for action in rule['actions']:
            action_parts = action.split('__')  
            new_action = action_parts[0] + '__' +  action_parts[1]
            if len(action_parts) == 3:
                if 'rules[' in action_parts[2]:            
                    action_params = str(action_parts[2]).split('_')
                    new_action_params = ''
                    for action_param in action_params:
                        if 'rules[' in action_param:
                            action_param_rules = action_param.replace('rules[', '').replace(']', '').split(',')
                            for action_param_rule in action_param_rules[:]:
                                if int(action_param_rule) == int(id):
                                    action_param_rules.remove(str(action_param_rule))
                                elif int(action_param_rule) > int(id):
                                    action_param_rules.remove(str(action_param_rule))
                                    action_param_rules.append(str(int(action_param_rule) - 1))
                            new_action_params += 'rules['   
                            for action_param_rule in action_param_rules:
                                new_action_params += action_param_rule + ','
                            new_action_params = new_action_params[:-1]
                            new_action_params += ']_'
                        else:
                            new_action_params += action_param + '_'
                    new_action += '__' +  new_action_params[:-1]
                else:    
                    new_action += '__' +  action_parts[2]            
            new_rule['actions'].append(new_action)
        orchestration_rule_rules_new.append(new_rule)
                    
    actions = [{
        'action': 'edit_orchestration_rule_rules',
        'username': request.user.username,
        'params': {
            'orchestration_rule_id': orchestration_rule_id,
            'region': 'ireland',
            'rules': orchestration_rule_rules_new
        }
    }]
        
    f = open( '../action_files/' + str(int(time.time() * 1e3)) + '.json', 'w+', encoding='UTF-8')
    f.write( json.dumps(actions) )
    f.close()                    
    return Response('OK')

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def edit_rules(request):
    if not 'orchestration_rule_id' in request.data:
        return Response('request must has param orchestration_rule_id', status=status.HTTP_400_BAD_REQUEST)
    if not 'rules' in request.data:
        return Response('request must has param rules', status=status.HTTP_400_BAD_REQUEST)
                
    orchestration_rule_id = request.data['orchestration_rule_id']
    rules = json.loads(request.data['rules'])
        
    if not orchestration_rule_exist(orchestration_rule_id=orchestration_rule_id):
        return Response('orchestration rule does not exist', status=status.HTTP_400_BAD_REQUEST)
                        
    actions = [{
        'action': 'edit_orchestration_rule_rules',
        'username': request.user.username,
        'params': {
            'orchestration_rule_id': orchestration_rule_id,
            'region': 'ireland',
            'rules': rules
        }
    }]
        
    f = open( '../action_files/' + str(int(time.time() * 1e3)) + '.json', 'w+', encoding='UTF-8')
    f.write( json.dumps(actions) )
    f.close()                    
    return Response('OK')

    

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def fetch(request):
    orchestration_rule_id = None
    if request.GET.get("orchestration_rule_id") is not None:
        orchestration_rule_id = request.GET.get("orchestration_rule_id")
    use = None
    if request.GET.get("use") is not None:
        use = request.GET.get("use")
    orchestration_rules = []
    orchestration_rules_folder = '../orchestration_rules'
    for orchestration_rule_file in os.listdir(orchestration_rules_folder):
        if os.path.exists(orchestration_rules_folder + '/' + orchestration_rule_file + '/config.json'):
            orchestration_rule = None
            if orchestration_rule_id is not None:
                if str(orchestration_rule_id) == str(orchestration_rule_file):
                    orchestration_rule = json.loads(open(orchestration_rules_folder + '/' + orchestration_rule_file + '/config.json', 'r', encoding='UTF-8').read())
                    if use is not None and 'use' in orchestration_rule and orchestration_rule['use'] != use:
                        continue
            else:
                orchestration_rule = json.loads(open(orchestration_rules_folder + '/' + orchestration_rule_file + '/config.json', 'r', encoding='UTF-8').read())
                if use is not None and 'use' in orchestration_rule and orchestration_rule['use'] != use:
                    continue
            if orchestration_rule is not None:
                rules = json.loads(open(orchestration_rules_folder + '/' + orchestration_rule_file + '/rules.json', 'r', encoding='UTF-8').read())
                orchestration_rule['rules'] = rules
                target = json.loads(open(orchestration_rules_folder + '/' + orchestration_rule_file + '/target.json', 'r', encoding='UTF-8').read())
                orchestration_rule['target'] = target
                orchestration_rules.append(orchestration_rule)
    return Response(orchestration_rules)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def fetch_target_params(request):
    strategy = None
    if 'strategy' in request.GET:
        strategy = request.GET.get("strategy")
   
    orchestration_rules_file = '../base/orchestration_rules.json'
    orchestration_rules = json.loads(open(orchestration_rules_file, 'r', encoding='UTF-8').read())    
    
    if strategy is None:
        return Response(orchestration_rules['target_strategy_params'])
    return Response(orchestration_rules['target_strategy_params'][strategy])


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def fetch_rule_actions(request):
    if not 'orchestration_rule_id' in request.GET:
        return Response('request must has param orchestration_rule_id', status=status.HTTP_400_BAD_REQUEST)
    orchestration_rule_id = request.GET.get("orchestration_rule_id")
    region = 'ireland'
    
    if not orchestration_rule_exist(orchestration_rule_id=orchestration_rule_id):
        return Response('orchestration rule does not exist', status=status.HTTP_400_BAD_REQUEST)
    
    orchestration_rule_config_file = '../orchestration_rules/' + orchestration_rule_id + '/config.json'
    orchestration_rule_config = json.loads(open(orchestration_rule_config_file, 'r', encoding='UTF-8').read())
    orchestration_rule_members = orchestration_rule_config['members']
    
    orchestration_rules_file = '../base/orchestration_rules_new.json'
    orchestration_rules = json.loads(open(orchestration_rules_file, 'r', encoding='UTF-8').read())
    
    for rule_action in orchestration_rules['rule_actions']:
        match rule_action['name']:
            case 'or':
                for rule_action_verb in rule_action['verbs']:
                    rule_action_verb['available_members'].append('or_' + orchestration_rule_id + '_' + region)
            case 'bot':
                for rule_action_verb in rule_action['verbs']:
                    rule_action_verb['available_members'] = orchestration_rule_members
            
    return Response(orchestration_rules['rule_actions'])

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def fetch_available_strategies(request):   
    orchestration_rules_file = '../base/orchestration_rules_new.json'
    orchestration_rules = json.loads(open(orchestration_rules_file, 'r', encoding='UTF-8').read())    
    return Response(orchestration_rules['strategies'])

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def fetch_available_rule_actions(request):
    if not 'strategy' in request.GET:
        return Response('request must has param strategy', status=status.HTTP_400_BAD_REQUEST)
    strategy = request.GET.get("strategy")
    orchestration_rules_file = '../base/orchestration_rules_new.json'
    orchestration_rules = json.loads(open(orchestration_rules_file, 'r', encoding='UTF-8').read())    
    available_rule_actions = {}
    for rule_action in orchestration_rules['rule_actions']:
        for rule_action_verb in rule_action['verbs']:
            if strategy in rule_action_verb['strategies']:
                if rule_action['name'] not in available_rule_actions:
                    available_rule_actions[rule_action['name']] = []
                del rule_action_verb['strategies']
                available_rule_actions[rule_action['name']].append(rule_action_verb)
    return Response(available_rule_actions)

def orchestration_rule_exist(orchestration_rule_id: str) -> bool:
    orchestration_rule_config_file = '../orchestration_rules/' + orchestration_rule_id + '/config.json'
    return os.path.exists(orchestration_rule_config_file)

def add_attributes_values_to_params(target_strategy_params: list, params: dict, attributes_values: dict) -> str:
    for param in target_strategy_params:
        param_name = param['name']
        param_type = param['type']
        if not param_name in attributes_values:
            raise ValueError('request param ' + param_name + ' must be like ' + json_param_format)
        elif param_type == 'json':
            json_param_format = param['format']
            json_param_value = attributes_values[param_name]
            for p_f in json_param_format:
                if not p_f in json_param_value:
                    raise ValueError('request param ' + param_name + ' must be like ' + json_param_format)
                if json_param_format[p_f] == 'int':
                    json_param_value[p_f] = int(json_param_value[p_f])
                elif json_param_format[p_f] == 'float':
                    json_param_value[p_f] = float(json_param_value[p_f])
                elif json_param_format[p_f] == 'str':
                    json_param_value[p_f] = str(json_param_value[p_f])
                elif json_param_format[p_f] == 'bool':
                    json_param_value[p_f] = bool(json_param_value[p_f])
                params[param_name] = json_param_value
        elif param_type == 'json_array':
            json_param_format = param['format']
            json_param_value = attributes_values[param_name]
            if len(json_param_value) == 0:
                raise ValueError('request param ' + param_name + ' list must has values')
            json_param_value_new = []
            for json_param_v in json_param_value:
                json_param_v_new = {}
                for p_f in json_param_format:
                    if not p_f in json_param_v:
                        raise ValueError('request param ' + param_name + ' must be like ' + json_param_format)
                    if json_param_format[p_f] == 'int':
                        json_param_v_new[p_f] = int(json_param_v[p_f])
                    elif json_param_format[p_f] == 'float':
                        json_param_v_new[p_f] = float(json_param_v[p_f])
                    elif json_param_format[p_f] == 'str':
                        json_param_v_new[p_f] = str(json_param_v[p_f])
                    elif json_param_format[p_f] == 'bool':
                        json_param_v_new[p_f] = bool(json_param_v[p_f])
                json_param_value_new.append(json_param_v_new)
            params[param_name] = json_param_value_new
                                   
        else:
            if param_type == 'int':
                params[param_name] = int(attributes_values[param_name])
            elif param_type == 'float':
                params[param_name] = float(attributes_values[param_name])
            elif param_type == 'str':
                params[param_name] = str(attributes_values[param_name])
            elif param_type == 'bool':
                params[param_name] = bool(attributes_values[param_name])
    
    return params
    