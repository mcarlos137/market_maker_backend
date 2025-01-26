import json
import os
import time
from datetime import datetime
import psycopg2
from psycopg2 import Error
from damexCommons.tools.utils import BASE_PATH, add_data_exchange_file
from tools.utils import get_pnl_values, get_ticker_last_price

exchanges_markets = set()

with open(BASE_PATH + '/exchanges_markets.json', 'r', encoding='UTF-8') as f:
    values = json.load(f)
    for val in values:
        if val['market'] == 'NONE':
            continue
        exchanges_markets.add(val['exchange'] + '__' + val['market'])
        
print('exchanges_markets', exchanges_markets)

OPERATION = 'current_pnl'

for exchange_market in exchanges_markets:
    exchange = exchange_market.split('__')[0]
    market = exchange_market.split('__')[1]
    exchange_folder = BASE_PATH + '/exchange_files/' + exchange
    if not os.path.exists(exchange_folder):
        os.makedirs(exchange_folder)
    operation_exchange_folder = exchange_folder + '/' + OPERATION
    if not os.path.exists(operation_exchange_folder):
        os.makedirs(operation_exchange_folder)
    market_operation_exchange_folder = operation_exchange_folder + '/' + market
    if not os.path.exists(market_operation_exchange_folder):
        os.makedirs(market_operation_exchange_folder)

    market_operation_exchange_old_folder = BASE_PATH + '/exchange_files_old/' + exchange + '/' + OPERATION + '/' + market

current_time = None

while True:
    if current_time is None:
        current_time = int(datetime.now().replace(second=0, microsecond=0).timestamp() * 1000) - (60 * 1000)
    initial_time = current_time - (60 * 1000)
    print('=====================================================')
    print('current_time', current_time)
    print('initial_time', initial_time)
    try:
        connection = psycopg2.connect(user="postgres",
                                      password="Telefonica18.",
                                      host="mm-prod.ci9tegrkvi4b.eu-west-1.rds.amazonaws.com",
                                      port="5432",
                                      database="mm_prod")

        cursor = connection.cursor()

        data = {}
        
        #fee_factor = 0.001
        
        query = '''SELECT t.base_asset, t.quote_asset, t.side, t.amount, t.price, t.fee, t.exchange
                    FROM (
                        (SELECT public."TRADES_NEW".base_asset, public."TRADES_NEW".quote_asset, public."TRADES_NEW".trade_type AS side, public."TRADES_NEW".amount, public."TRADES_NEW".price, public."TRADES_NEW".trade_fee AS fee, public."EXCHANGES".name AS exchange FROM public."TRADES_NEW" JOIN public."BOT_SPRINTS" ON public."BOT_SPRINTS".id = public."TRADES_NEW".bot_sprint_id JOIN public."EXCHANGES" ON public."EXCHANGES".id = public."BOT_SPRINTS".exchange_id WHERE public."TRADES_NEW".timestamp <= %s AND public."TRADES_NEW".timestamp > %s) 
                        UNION ALL 
                        (SELECT maker_bots."TRADES".base_asset, maker_bots."TRADES".quote_asset, (CASE WHEN maker_bots."TRADES".side = 1 THEN %s ELSE %s END) AS side, maker_bots."TRADES".amount, maker_bots."TRADES".price, maker_bots."TRADES".fee, maker_bots."TRADES".exchange FROM maker_bots."TRADES" WHERE maker_bots."TRADES".timestamp <= %s AND maker_bots."TRADES".timestamp > %s) 
                        UNION ALL 
                        (SELECT taker_bots."TRADES".base_asset, taker_bots."TRADES".quote_asset, (CASE WHEN taker_bots."TRADES".side = 1 THEN %s ELSE %s END) AS side, taker_bots."TRADES".amount, taker_bots."TRADES".price, taker_bots."TRADES".fee, taker_bots."TRADES".exchange FROM taker_bots."TRADES" WHERE taker_bots."TRADES".timestamp <= %s AND taker_bots."TRADES".timestamp > %s) 
                        UNION ALL 
                        (SELECT vol_bots."TRADES".base_asset, vol_bots."TRADES".quote_asset, (CASE WHEN vol_bots."TRADES".side = 1 THEN %s ELSE %s END) AS side, vol_bots."TRADES".amount, vol_bots."TRADES".price, vol_bots."TRADES".fee, vol_bots."TRADES".exchange FROM vol_bots."TRADES" WHERE vol_bots."TRADES".timestamp <= %s AND vol_bots."TRADES".timestamp > %s)
                    ) t;''' % (
            current_time, 
            initial_time,
            '\'BUY\'',
            '\'SELL\'',
            current_time, 
            initial_time,
            '\'BUY\'',
            '\'SELL\'',
            current_time, 
            initial_time,
            '\'BUY\'',
            '\'SELL\'',
            current_time, 
            initial_time
        )
        #query = 'SELECT "TRADES_NEW".base_asset, "TRADES_NEW".quote_asset, "TRADES_NEW".trade_type, "TRADES_NEW".amount, "TRADES_NEW".price, "TRADES_NEW".trade_fee, "EXCHANGES".name FROM "TRADES_NEW" JOIN "BOT_SPRINTS" ON "BOT_SPRINTS".id = "TRADES_NEW".bot_sprint_id JOIN "EXCHANGES" ON "EXCHANGES".id = "BOT_SPRINTS".exchange_id WHERE timestamp <= %s AND timestamp > %s;' % (current_time, initial_time)
        #query = 'SELECT "TRADES_NEW".base_asset, "TRADES_NEW".quote_asset, "TRADES_NEW".trade_type, "TRADES_NEW".amount, "TRADES_NEW".price, "TRADES_NEW".trade_fee, "EXCHANGES".name FROM "TRADES_NEW" JOIN "BOT_SPRINTS" ON "BOT_SPRINTS".id = "TRADES_NEW".bot_sprint_id JOIN "EXCHANGES" ON "EXCHANGES".id = "BOT_SPRINTS".exchange_id WHERE bot_sprint_id = %s OR bot_sprint_id = %s ORDER BY timestamp ASC LIMIT 20;' % (255, 256)
        cursor.execute(query)
        records = cursor.fetchall()
                
        print('records', records)    
        
        if len(records) > 0:
            data = get_pnl_values(data_set=records, look_previous_data=True, all_in_one_exchange_market=False)
                
        for exchange_market in exchanges_markets:
            if exchange_market in data:
                continue
            data[exchange_market] = {
                'position': 0,
                'position_shifted': 0,
                'vwap': None,
                'realized_pnl_sum': 0,
                'unrealized_pnl': 0,
                'total_pnl': 0,
            }
            exchange = exchange_market.split('__')[0]
            market = exchange_market.split('__')[1]
            #print('exchange_market', exchange, market)
            
            info_file_path = BASE_PATH + '/exchange_files/' + exchange + '/current_pnl/' + market + '/info.json'
            market_operation_exchange_folder = BASE_PATH + '/exchange_files/' + exchange + '/' + OPERATION + '/' + market
            market_operation_exchange_old_folder = BASE_PATH + '/exchange_files_old/' + exchange + '/' + OPERATION + '/' + market
            if os.path.exists(info_file_path):
                info = json.loads(open(info_file_path, 'r', encoding='UTF-8').read())
                #print('info', info['last_file_name'])
                if not 'reset' in info:    
                    pnl_file_path = market_operation_exchange_folder + '/' + info['last_file_name']
                    if not os.path.exists(pnl_file_path):
                        pnl_file_path = market_operation_exchange_old_folder + '/' + info['last_file_name']
                    data_previous = json.loads(open(pnl_file_path, 'r', encoding='UTF-8').read())
                    #print('data_previous', data_previous)
                    data[exchange_market]['position'] = data_previous['values'][0]['value']
                    data[exchange_market]['position_shifted'] = data_previous['values'][1]['value']
                    data[exchange_market]['vwap'] = data_previous['values'][2]['value']
                    data[exchange_market]['realized_pnl_sum'] = data_previous['values'][3]['value']
                    
                    current_price = get_ticker_last_price(exchange=exchange, market=market)

                    if not data[exchange_market]['vwap'] is None:
                        data[exchange_market]['unrealized_pnl'] = (current_price - data[exchange_market]['vwap']) * data[exchange_market]['position']
                        data[exchange_market]['total_pnl'] = data[exchange_market]['realized_pnl_sum'] + data[exchange_market]['unrealized_pnl']
                    
                else:
                    print('delete reset_current_pnl from info.json')
                    del info['reset']
                    with open(info_file_path, "w", encoding='UTF-8') as jsonFile:
                        json.dump(info, jsonFile)
                                        
        for exchange_market in data:
            exchange = exchange_market.split('__')[0]
            market = exchange_market.split('__')[1]
            
            current_pnl_data = {
                'time': current_time,
                'values': [
                    {
                        'type': 'position',
                        'value': data[exchange_market]['position'],
                    },
                    {
                        'type': 'position_shifted',
                        'value': data[exchange_market]['position_shifted'],
                    },
                    {
                        'type': 'vwap',
                        'value': data[exchange_market]['vwap'],
                    },
                    {
                        'type': 'realized_pnl_sum',
                        'value': data[exchange_market]['realized_pnl_sum'],
                    },
                    {
                        'type': 'unrealized_pnl',
                        'value': data[exchange_market]['unrealized_pnl'],
                    },
                    {
                        'type': 'total_pnl',
                        'value': data[exchange_market]['total_pnl'],
                    }
                ]
            }
            add_data_exchange_file(file_name=(str(current_time) + '.json'), data=current_pnl_data, exchange=exchange, operation=OPERATION, market=market)

        print('=====================================================')
        current_time = None
    except (Exception, Error) as error:
        print("Error while connecting to PostgreSQL", error)
    finally:
        if (connection):
            cursor.close()
            connection.close()
            print("PostgreSQL connection is closed")
        if current_time is None:
            time.sleep(60)
        else:
            #Retry
            print('Retry--------')
            time.sleep(1)
