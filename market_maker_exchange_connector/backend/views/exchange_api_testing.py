import json
import time
import os
import asyncio
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from ..utils import DATA_FOLDER, DATA_OLD_FOLDER
from damexCommons.tools.exchange import get_order_book_price

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def post_trade(request):
    if not 'market' in request.data:
        return Response('request must has param market', status=status.HTTP_400_BAD_REQUEST)
    if not 'amount' in request.data:
        return Response('request must has param amount', status=status.HTTP_400_BAD_REQUEST)
    if not 'currency' in request.data:
        return Response('request must has param currency', status=status.HTTP_400_BAD_REQUEST)
    if not 'side' in request.data:
        return Response('request must has param side', status=status.HTTP_400_BAD_REQUEST)
    market = request.data['market']
    amount = float(request.data['amount'])
    currency = request.data['currency']
    side = request.data['side']
    if not 'price' in request.data:
        order_book_price = asyncio.run(get_order_book_price(base_asset=market.split('-')[0], quote_asset=market.split('-')[1], currency=currency, side=side, amount=amount))
        price = order_book_price['price']
    else:
        price = request.data['price']
    current_time = int(time.time() * 1e3)
    file_name = str(current_time) + '.json'
    trades_folder = '%s/%s/%s/%s' % (DATA_FOLDER, 'APP_TESTING', 'trades', market)
    trade = {
        'timestamp': current_time,
        'price': price,
        'amount': amount,
        'currency': currency,
        'side': side
    }
    f = open(trades_folder + '/' + file_name, 'w+', encoding='UTF-8')
    f.write(json.dumps(trade))
    f.close()
    if os.path.exists(trades_folder + '/info.json'):
        with open(trades_folder + '/info.json', "r", encoding='UTF-8') as jsonFile:
            info = json.load(jsonFile)
    else:
        info = {}
    info['last_file_name'] = file_name
    with open(trades_folder + '/info.json', "w", encoding='UTF-8') as jsonFile:
        json.dump(info, jsonFile)
    return Response(price)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_last_price(request):
    market = request.GET.get("market")
    if market == 'DAMEX-USDT':
        trades_folder = '%s/%s/%s/%s' % (DATA_FOLDER, 'APP_TESTING', 'trades', market)
        trades_old_folder = '%s/%s/%s/%s' % (DATA_OLD_FOLDER, 'APP_TESTING', 'trades', market)
        info_trades = json.loads(open(trades_folder + '/info.json', 'r', encoding='UTF-8').read())
        if os.path.exists(trades_folder + '/' + info_trades['last_file_name']):
            last_trade = json.loads(open(trades_folder + '/' + info_trades['last_file_name'], 'r', encoding='UTF-8').read())
        else:
            last_trade = json.loads(open(trades_old_folder + '/' + info_trades['last_file_name'], 'r', encoding='UTF-8').read())
        return Response(last_trade['price'])
    else:
        return Response(0)
    

