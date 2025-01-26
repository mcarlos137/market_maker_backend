import json
import time
import os
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from ..utils import get_new_file_time, get_minutes

@api_view(['GET'])
@permission_classes([AllowAny])
def fetch(request):
    
    if not 'arbitrage_type' in request.GET:
        return Response('request must has param arbitrage_type', status=status.HTTP_400_BAD_REQUEST)
    
    arbitrage_type = request.GET.get("arbitrage_type")
    
    period = None
    size = 10
    if 'period' in request.GET:
        period = request.GET.get("period")
    if 'size' in request.GET:
        size = int(request.GET.get("size"))
        
    arbitrage_opportunities = []
     
    if period is None:
        last_file_name = json.loads(open('../arbitrage_opportunities/' + arbitrage_type + '/' + 'info.json', 'r', encoding='UTF-8').read())['last_file_name']
        last_arbitrage_opportunities = json.loads(open('../arbitrage_opportunities/' + arbitrage_type + '/' + last_file_name, 'r', encoding='UTF-8').read())
        
        for key in last_arbitrage_opportunities:
            init_time = last_arbitrage_opportunities[key]['init_time']
            last_time = last_arbitrage_opportunities[key]['last_time']
            if arbitrage_type == 'simple':
                arbitrage_opportunity = {
                    'exchange_buy': key.split('__')[0],
                    'exchange_sell': key.split('__')[1],
                    'pair': key.split('__')[2],
                    'init_time': init_time,
                    'last_time': last_time,
                    'period_in_secs': int((last_time - init_time) / 1e3),
                    'profitability_percentage': last_arbitrage_opportunities[key]['profitability_percentage'],
                    'depth': last_arbitrage_opportunities[key]['depth'],
                    'profitability_amount': last_arbitrage_opportunities[key]['profitability_amount'],
                    'profitability_asset': last_arbitrage_opportunities[key]['profitability_asset'],
                }
                if 'buy_price' in  last_arbitrage_opportunities[key]:
                    arbitrage_opportunity['buy_price'] = last_arbitrage_opportunities[key]['buy_price']  
                if 'sell_price' in  last_arbitrage_opportunities[key]:
                    arbitrage_opportunity['sell_price'] = last_arbitrage_opportunities[key]['sell_price']   
                arbitrage_opportunities.append(arbitrage_opportunity)
            elif arbitrage_type == 'triple':
                arbitrage_opportunities.append({
                    'exchange': key.split('__')[0],
                    'pair_1': key.split('__')[1],
                    'pair_2': key.split('__')[2],
                    'pair_3': key.split('__')[3],
                    'variation': last_arbitrage_opportunities[key]['variation'],
                    'init_time': init_time,
                    'last_time': last_time,
                    'period_in_secs': int((last_time - init_time) / 1e3),
                    'profitability_percentage': last_arbitrage_opportunities[key]['profitability_percentage'],
                    'depth': last_arbitrage_opportunities[key]['depth'],
                    'profitability_amount': last_arbitrage_opportunities[key]['profitability_amount'],
                    'profitability_asset': last_arbitrage_opportunities[key]['profitability_asset'],
                })
    else:
        current_time = int(time.time() * 1e3)
        i = 0
        while len(arbitrage_opportunities) <= size and i <= 20:
            i += 1
            current_time -= int(get_minutes(period)) * 60 * 1e3
            new_file_time = get_new_file_time(current_time, period)
            arbitrage_opportunity_period_file = '../arbitrage_opportunities/' + arbitrage_type + '/' + period + '/' + str(new_file_time) + '.json'
            print('arbitrage_opportunity_period_file', arbitrage_opportunity_period_file)
            if not os.path.isfile(arbitrage_opportunity_period_file):
                continue
            arbitrage_opportunity_period = json.loads(open(arbitrage_opportunity_period_file, 'r', encoding='UTF-8').read())
            arbitrage_opportunities_period = []
            for key in arbitrage_opportunity_period:
                init_time = arbitrage_opportunity_period[key]['init_time']
                last_time = arbitrage_opportunity_period[key]['last_time']
                if arbitrage_type == 'simple':
                    arbitrage_opportunities_period.append({
                        'exchange_buy': key.split('__')[0],
                        'exchange_sell': key.split('__')[1],
                        'pair': key.split('__')[2],
                        'init_time': init_time,
                        'last_time': last_time,
                        'period_in_secs': arbitrage_opportunity_period[key]['period_in_secs'],
                        'count': arbitrage_opportunity_period[key]['count'],
                        'max_amount': arbitrage_opportunity_period[key]['max_amount'],
                        'max_percentage': arbitrage_opportunity_period[key]['max_percentage'],
                        'max_depth': arbitrage_opportunity_period[key]['max_depth'],
                        'profitability_asset': arbitrage_opportunity_period[key]['profitability_asset'],
                    })
                elif arbitrage_type == 'triple':
                    arbitrage_opportunities_period.append({
                        'exchange': key.split('__')[0],
                        'pair_1': key.split('__')[1],
                        'pair_2': key.split('__')[2],
                        'pair_3': key.split('__')[3],
                        'variation': last_arbitrage_opportunities[key]['variation'],
                        'init_time': init_time,
                        'last_time': last_time,
                        'period_in_secs': arbitrage_opportunity_period[key]['period_in_secs'],
                        'count': arbitrage_opportunity_period[key]['count'],
                        'max_amount': arbitrage_opportunity_period[key]['max_amount'],
                        'max_percentage': arbitrage_opportunity_period[key]['max_percentage'],
                        'max_depth': arbitrage_opportunity_period[key]['max_depth'],
                        'profitability_asset': arbitrage_opportunity_period[key]['profitability_asset'],
                    })
            
            arbitrage_opportunities.append({'time': new_file_time, 'data': arbitrage_opportunities_period})
            
    return Response(arbitrage_opportunities)    