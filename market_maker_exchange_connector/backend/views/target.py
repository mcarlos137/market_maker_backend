import json
import time
import os
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create(request):
    if not 'target_id' in request.data:
        return Response('request must has param target_id', status=status.HTTP_400_BAD_REQUEST)
    if not 'initial_timestamp' in request.data:
        return Response('request must has param initial_timestamp', status=status.HTTP_400_BAD_REQUEST)
    if not 'final_timestamp' in request.data:
        return Response('request must has param final_timestamp', status=status.HTTP_400_BAD_REQUEST)
    if not 'asset' in request.data:
        return Response('request must has param asset', status=status.HTTP_400_BAD_REQUEST)
    if not 'initial_asset_amount' in request.data:
        return Response('request must has param initial_asset_amount', status=status.HTTP_400_BAD_REQUEST)
    if not 'operation' in request.data:
        return Response('request must has param operation', status=status.HTTP_400_BAD_REQUEST)
    if not 'operation_amount' in request.data:
        return Response('request must has param operation_amount', status=status.HTTP_400_BAD_REQUEST)
        
    target_id = request.data['target_id']
    initial_timestamp = int(request.data['initial_timestamp'])
    final_timestamp = int(request.data['final_timestamp'])
    asset = request.data['asset']
    initial_asset_amount = float(request.data['initial_asset_amount'])
    operation = request.data['operation']
    operation_amount = float(request.data['operation_amount'])
                
    action = {
        'action': 'create_target',
        'username': request.user.username,
        'params': {
            'target_id': target_id, 
            'initial_timestamp': initial_timestamp, 
            'final_timestamp': final_timestamp,
            'asset': asset,
            'initial_asset_amount': initial_asset_amount,
            'operation': operation,
            'operation_amount': operation_amount,
            'status': 'not_completed',
            'region': 'ireland'
        }
    }
        
    actions = [action]
    f = open( '../action_files/' + str(int(time.time() * 1e3)) + '.json', 'w+', encoding='UTF-8')
    f.write( json.dumps(actions) )
    f.close()                    
    return Response('OK')

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_failed(request):
    if not 'target_id' in request.data:
        return Response('request must has param target_id', status=status.HTTP_400_BAD_REQUEST)
        
    target_id = request.data['target_id']
                
    action = {
        'action': 'create_target',
        'username': request.user.username,
        'params': {
            'target_id': target_id, 
            'status': 'failed',
            'region': 'ireland'
        }
    }
        
    actions = [action]
    f = open( '../action_files/' + str(int(time.time() * 1e3)) + '.json', 'w+', encoding='UTF-8')
    f.write( json.dumps(actions) )
    f.close()                    
    return Response('OK')


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def edit(request):
    if not 'target_id' in request.data:
        return Response('request must has param target_id', status=status.HTTP_400_BAD_REQUEST)
    if not 'new_attributes_values' in request.data:
        return Response('request must has param new_attributes_values', status=status.HTTP_400_BAD_REQUEST)
    
    target_id = request.data['target_id']
    new_attributes_values = json.loads(request.data['new_attributes_values'])
    
    target = add_new_attributes_values_to_target(target_id=target_id, new_attributes_values=new_attributes_values)
    target['region'] = 'ireland'
    if target is not None:                         
        actions = [{
            'action': 'edit_target',
            'username': request.user.username,
            'params': target,
        }]
        f = open( '../action_files/' + str(int(time.time() * 1e3)) + '.json', 'w+', encoding='UTF-8')
        f.write( json.dumps(actions) )
        f.close()                    
        return Response('OK')
    
    return Response('FAILED')
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def fetch(request):
    if not 'target_id' in request.GET:
        return Response('request must has param target_id', status=status.HTTP_400_BAD_REQUEST)
    target_id = request.GET.get("target_id")
    target_file = '../target_files/' + target_id + '.json'
    if os.path.exists(target_file):
        return Response(json.loads(open(target_file, 'r', encoding='UTF-8').read()))
    
    return Response({})    
         
    
def add_new_attributes_values_to_target(target_id: str, new_attributes_values: dict):
    attributes = ['status']
    target_file = '../target_files/' + target_id + '.json'
    if os.path.exists(target_file):
        target = json.loads(open(target_file, 'r', encoding='UTF-8').read())
        for new_attribute in new_attributes_values:
            if new_attribute in attributes:
                target[new_attribute] = new_attributes_values[new_attribute]   
        return target
    return None 