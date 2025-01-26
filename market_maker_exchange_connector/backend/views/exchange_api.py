import json
import time
import os
import asyncio
import requests
from datetime import datetime
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from damexCommons.tools.dbs import get_exchange_db
from damexCommons.tools.exchange import get_order_book_price, get_main_price as exchange_get_main_price
from ..utils import DATA_FOLDER, DATA_OLD_FOLDER

exchange_db = get_exchange_db(db_connection='exchange_connector')

#DAMEX APP - CHECK
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
        base_asset: str = market.split('-')[0]
        quote_asset: str = market.split('-')[1]
        order_book_price = asyncio.run(get_order_book_price(base_asset=base_asset, quote_asset=quote_asset, currency=currency, side=side, amount=amount))
        price = order_book_price['price']
    else:
        price = request.data['price']
    current_time = int(time.time() * 1e3)
    file_name = str(current_time) + '.json'
    trades_folder = '%s/%s/%s/%s' % (DATA_FOLDER, 'APP', 'trades', market)
    trade = {
        'timestamp': current_time,
        'price': price,
        'amount': amount,
        'currency': currency,
        'side': side,
        'exchange': 'APP'
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
    if 'last_trade_price' in info and float(info['last_trade_price']) != float(price):
        info['last_trade_price'] = price
    elif not 'last_trade_price' in info:
        info['last_trade_price'] = price
    if market.split('-')[1] == currency:
        amount = amount / price
    last_trade = {'timestamp': int(time.time() * 1000), 'price': str(price), 'amount': str(amount), 'side': str(side)}
    if 'last_trades' in info:
        info['last_trades'].append(last_trade)
        if len(info['last_trades']) > 101:
            info['last_trades'].pop(0)
    elif not 'last_trades' in info:
        info['last_trades'] = [last_trade]
    with open(trades_folder + '/info.json', "w", encoding='UTF-8') as jsonFile:
        json.dump(info, jsonFile)
    return Response(price)

#MM DASHBOARD, MM - GOOD
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_main_price(request):
    if not 'market' in request.GET:
        return Response('request must has param market', status=status.HTTP_400_BAD_REQUEST)
    market = request.GET.get("market")
      
    return Response(asyncio.run(exchange_get_main_price(base_asset=market.split('-')[0], quote_asset=market.split('-')[1])))    

#MM - CHECK    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_order_book(request):
    if not 'market' in request.GET:
        return Response('request must has param market', status=status.HTTP_400_BAD_REQUEST)
    if not 'size' in request.GET:
        return Response('request must has param size', status=status.HTTP_400_BAD_REQUEST)
    market = request.GET.get("market")
    size = int(request.GET.get("size"))
    return Response(asyncio.run(exchange_db.get_order_book_db(base_asset=market.split('-')[0], quote_asset=market.split('-')[1], size=size)))

#DAMEX APP or MM - CHECK
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_trades(request):
    if not 'market' in request.GET:
        return Response('request must has param market', status=status.HTTP_400_BAD_REQUEST)
    if not 'source' in request.GET:
        return Response('request must has param source', status=status.HTTP_400_BAD_REQUEST)
    market = request.GET.get("market")
    source = request.GET.get("source")
    start_timestamp = request.GET.get("start_timestamp") if request.GET.get("start_timestamp") else None
    end_timestamp = request.GET.get("end_timestamp") if request.GET.get("end_timestamp") else None
    
    trades = []
    trades_folder = '%s/%s/%s/%s' % (DATA_FOLDER, source, 'trades', market)
    trades_folder_old = '%s/%s/%s/%s' % (DATA_OLD_FOLDER, source, 'trades', market)
    
    for trade_file in os.listdir(trades_folder_old):
        if os.path.isdir(trades_folder_old + '/' + trade_file):
            continue
        timestamp = int(trade_file.replace('.json', ''))
        if start_timestamp is not None and timestamp < int(start_timestamp):
            continue
        if end_timestamp is not None and timestamp > int(end_timestamp):
            continue
        trade = json.loads(open(trades_folder_old + '/' + trade_file, 'r', encoding='UTF-8').read())
        trades.append(trade)
        
    for trade_file in os.listdir(trades_folder):
        if os.path.isdir(trades_folder + '/' + trade_file):
            continue
        if trade_file == 'info.json':
            continue
        timestamp = int(trade_file.replace('.json', ''))
        if start_timestamp is not None and timestamp < int(start_timestamp):
            continue
        if end_timestamp is not None and timestamp > int(end_timestamp):
            continue
        trade = json.loads(open(trades_folder + '/' + trade_file, 'r', encoding='UTF-8').read())
        trades.append(trade)
            
    trades_sorted = sorted(trades, key=lambda x: x['timestamp'], reverse=False)
            
    return Response(trades_sorted)

#MM - CHECK
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_last_trade(request):
    if not 'market' in request.GET:
        return Response('request must has param market', status=status.HTTP_400_BAD_REQUEST)
    if not 'source' in request.GET:
        return Response('request must has param source', status=status.HTTP_400_BAD_REQUEST)
    market = request.GET.get("market")
    source = request.GET.get("source")
    
    trades_info_file = '%s/%s/%s/%s/%s' % (DATA_FOLDER, source, 'trades', market, 'info.json')
    trades_info = json.loads(open(trades_info_file, 'r', encoding='UTF-8').read())
    last_trade = trades_info['last_trades'][len(trades_info['last_trades']) - 1]
    return Response(last_trade)

#MM - CHECK    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_inventory_values(request):
    if not 'exchange' in request.GET:
        return Response('request must has param exchange', status=status.HTTP_400_BAD_REQUEST)
    if not 'market' in request.GET:
        return Response('request must has param market', status=status.HTTP_400_BAD_REQUEST)
    exchange = request.GET.get("exchange")
    market = request.GET.get("market")
    operation = 'current_pnl'
    
    exchange_operation_market_folder = '%s/%s/%s/%s' % (DATA_FOLDER, exchange, operation, market)
    
    with open(exchange_operation_market_folder + '/info.json', "r", encoding='UTF-8') as jsonFile:
        info = json.load(jsonFile)
        pnl = json.loads(open(exchange_operation_market_folder + '/' + info['last_file_name'], 'r', encoding='UTF-8').read())
        inventory_values = {'timestamp': pnl['time']}
    
        for pnl_value in pnl['values']:
            if pnl_value['type'] == 'position':
                inventory_values['position'] = pnl_value['value']
            if pnl_value['type'] == 'vwap':
                inventory_values['vwap'] = pnl_value['value']

        return Response(inventory_values)

#MM DASHBOARD - GOOD    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_balance_resume(request):
    if not 'market' in request.GET:
        return Response('request must has param market', status=status.HTTP_400_BAD_REQUEST)
    if not 'initial_timestamp' in request.GET:
        return Response('request must has param initial_timestamp', status=status.HTTP_400_BAD_REQUEST)
    if not 'final_timestamp' in request.GET:
        return Response('request must has param final_timestamp', status=status.HTTP_400_BAD_REQUEST)
    
    market = request.GET.get("market")
    initial_timestamp = request.GET.get("initial_timestamp")
    final_timestamp = request.GET.get("final_timestamp")
    
    base_currency = market.split('-')[0]
    quote_currency = market.split('-')[1]
    
    exchanges = []
    
    if market == 'DAMEX-USDT':
        exchanges = ['bitmart', 'coinstore', 'mexc', 'tidex', 'ascendex', 'uniswap', 'pancakeswap']
    elif market == 'HOT-USDT':
        exchanges = ['binance']
    
    main_price = asyncio.run(exchange_get_main_price(base_asset=market.split('-')[0], quote_asset=market.split('-')[1]))
    
    initial_timestamp = int(datetime.fromtimestamp(int(initial_timestamp) / 1000).replace(second=(0), microsecond=0).timestamp() * 1000)
    final_timestamp = int(datetime.fromtimestamp(int(final_timestamp) / 1000).replace(second=(0), microsecond=0).timestamp() * 1000)

    balance_resume = {
        initial_timestamp: {},
        final_timestamp: {},
        'diff': {},
        'balance': {},
        'deposits': {},
        'withdrawals': {},
        'diff_operation': {},
        'mid_price': {},
        'balance_operation': {}
    }
    
    balance_resume['main_price'] = main_price
        
    for exchange in exchanges:
        balance_resume[initial_timestamp][exchange] = {}
        balance_resume[final_timestamp][exchange] = {}
        balance_resume['diff'][exchange] = {}
        balance_resume['balance'][exchange] = 0
        balance_resume['deposits'][exchange] = {'DAMEX': 0, 'USDT': 0}
        balance_resume['withdrawals'][exchange] = {'DAMEX': 0, 'USDT': 0}
        balance_resume['diff_operation'][exchange] = {'DAMEX': 0, 'USDT': 0}
        balance_resume['balance_operation'][exchange] = 0
        
        for currency in market.split('-'):
            balance_resume[initial_timestamp][exchange][currency] = 0
            balance_resume[final_timestamp][exchange][currency] = 0
            balance_resume['diff'][exchange][currency] = 0
        
        if exchange == 'uniswap' or exchange == 'pancakeswap':
            continue
          
        i = 0
        while i < 10 * 60 * 1e3:
            balance_initial_path = '%s/%s/%s/%s/%s' % (DATA_FOLDER, exchange, 'current_values', 'NONE', str(int(initial_timestamp - i)) + '.json')
            i += 60 * 1e3
            if os.path.isfile(balance_initial_path):
                break
        if not os.path.isfile(balance_initial_path):
            i = 0
            while i < 10 * 60 * 1e3:
                balance_initial_path = '%s/%s/%s/%s/%s' % (DATA_OLD_FOLDER, exchange, 'current_values', 'NONE', str(int(initial_timestamp - i)) + '.json')
                i += 60 * 1e3
                if os.path.isfile(balance_initial_path):
                    break

        if not os.path.isfile(balance_initial_path):
            continue
        balance_initial = json.loads(open(balance_initial_path, 'r', encoding='UTF-8').read())
                
        i = 0
        while i < 10 * 60 * 1e3:
            balance_final_path = '%s/%s/%s/%s/%s' % (DATA_FOLDER, exchange, 'current_values', 'NONE', str(int(final_timestamp - i)) + '.json')
            i += 60 * 1e3
            if os.path.isfile(balance_final_path):
                break
        if not os.path.isfile(balance_final_path):
            i = 0
            while i < 10 * 60 * 1e3:
                balance_final_path = '%s/%s/%s/%s/%s' % (DATA_OLD_FOLDER, exchange, 'current_values', 'NONE', str(int(final_timestamp - i)) + '.json')
                i += 60 * 1e3
                if os.path.isfile(balance_final_path):
                    break
        
        if not os.path.isfile(balance_final_path):
            continue
        balance_final = json.loads(open(balance_final_path, 'r', encoding='UTF-8').read())
                        
        for value in balance_initial['values']:
            if value['currency'] != base_currency and value['currency'] != quote_currency:
                continue
            balance_resume[initial_timestamp][exchange][value['currency']] = float(value['amount'])
            balance_resume['diff'][exchange][value['currency']] = -float(value['amount'])
            
        for value in balance_final['values']:
            if value['currency'] != base_currency and value['currency'] != quote_currency:
                continue
            balance_resume[final_timestamp][exchange][value['currency']] = float(value['amount'])
            balance_resume['diff'][exchange][value['currency']] = float(balance_resume['diff'][exchange][value['currency']]) + float(value['amount'])
            
            if value['currency'] == base_currency:
                balance_resume['balance'][exchange] = float(balance_resume['balance'][exchange]) + float(balance_resume['diff'][exchange][value['currency']] * main_price)  
            else:
                balance_resume['balance'][exchange] = float(balance_resume['balance'][exchange]) + float(balance_resume['diff'][exchange][value['currency']])
            
            balance_resume['diff_operation'][exchange][value['currency']] = balance_resume['diff'][exchange][value['currency']]
                    
    transfers = requests.get('https://mm.damex.io/transfers', timeout=7).json()
        
    currencies = {1: 'USDT', 2: 'DAMEX'}
    exchanges = {6: 'bitmart', 7: 'coinstore', 8: 'tidex', 9: 'mexc', 13: 'ascendex'}
             
    for transfer in transfers:
        exchange_id = transfer['exchange_id']
        currency = transfer['currency']
        timestamp = int(datetime.fromisoformat(transfer['executed_at']).timestamp() * 1e3)
        if timestamp < int(initial_timestamp) or timestamp > int(final_timestamp):
            continue
        balance_resume['deposits' if transfer['type'] == 1 else 'withdrawals'][exchanges[exchange_id]][currencies[currency]] = float(balance_resume['deposits' if transfer['type'] == 1 else 'withdrawals'][exchanges[exchange_id]][currencies[currency]]) + float(transfer['amount'])
        if transfer['type'] == 1:
            balance_resume['diff_operation'][exchanges[exchange_id]][currencies[currency]] = float(balance_resume['diff_operation'][exchanges[exchange_id]][currencies[currency]]) - float(transfer['amount'])
        else:
            balance_resume['diff_operation'][exchanges[exchange_id]][currencies[currency]] = float(balance_resume['diff_operation'][exchanges[exchange_id]][currencies[currency]]) + float(transfer['amount'])
            
    for exchange in balance_resume['diff_operation']:
        for currency in balance_resume['diff_operation'][exchange]:
            if currency == base_currency:
                balance_resume['balance_operation'][exchange] = float(balance_resume['balance_operation'][exchange]) + float(balance_resume['diff_operation'][exchange][currency] * main_price)  
            else:
                balance_resume['balance_operation'][exchange] = float(balance_resume['balance_operation'][exchange]) + float(balance_resume['diff_operation'][exchange][currency])
        
        if float(balance_resume['diff_operation'][exchange]['DAMEX']) == 0:
            continue
        mid_price = -1 * float(balance_resume['diff_operation'][exchange]['USDT']) / float(balance_resume['diff_operation'][exchange]['DAMEX'])
        if mid_price > 0:
            balance_resume['mid_price'][exchange] = -1 * float(balance_resume['diff_operation'][exchange]['USDT']) / float(balance_resume['diff_operation'][exchange]['DAMEX'])
        else:
            balance_resume['mid_price'][exchange] = None
                                            
    return Response(balance_resume)
