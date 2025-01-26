import pika
import time
import json
import os
import itertools
import sys
import logging
from threading import Thread
from math import comb
from logging.handlers import RotatingFileHandler
from damexCommons.base import TradeSide
from damexCommons.tools.dbs import get_exchange_db

class ArbitrageOpportunities:
        
    def __init__(self, arbitrage_type: str) -> None:
        self.arbitrage_type = arbitrage_type
        self.operation = 'arbitrage_opportunities_test'
        self.min_profitability_percentage = 0.01
        self.order_books = {}
        self.arbitrage_opportunities = {}
        
        exchange_db = get_exchange_db(db_connection='preprocessor')
        self.exchanges_info = exchange_db.fetch_exchanges_info_db()
        
        self.possible_arbitrage_opportunities= {}
        
        for exchange in self.exchanges_info:
            for market in self.exchanges_info[exchange]:
                if market not in self.possible_arbitrage_opportunities:
                    self.possible_arbitrage_opportunities[market] = {'exchanges': [], 'combinations': 0}
                self.possible_arbitrage_opportunities[market]['exchanges'].append(exchange)
        
        for market in self.possible_arbitrage_opportunities:
            self.possible_arbitrage_opportunities[market]['combinations'] = comb(len(self.possible_arbitrage_opportunities[market]['exchanges']), 2) * 2
        
        logging.basicConfig(
            level=logging.INFO, 
            handlers=[
                RotatingFileHandler(f"{self.operation}_{self.arbitrage_type}.log", mode='a', maxBytes=1024*1024*10, backupCount=10, encoding=None, delay=0),
                logging.StreamHandler()
            ],
            format="%(asctime)s %(levelname)s %(message)s"
        )
        
    def run(self):
        #self.arbitrage_opportunities = self.get_current_arbitrage_opportunities()
        #t = Thread(target=self.check_order_books, args=())
        #t.start()
        while True:
            connection = None
            channel = None 
            try:
                connection = pika.BlockingConnection(
                    pika.ConnectionParameters('172.20.143.247',
                        5672,
                        '/',
                        pika.PlainCredentials('test', 'test')
                    )
                )
                channel = connection.channel()
                channel.basic_consume(queue='order_book',
                    auto_ack=True,
                    on_message_callback=self.callback
                )
                channel.start_consuming()
            except Exception as e:
                logging.error('----------------- error with channel ----------------- %s', e)
                self.order_books = {}
            finally:
                #if channel.is_open:    
                #    channel.stop_consuming()
                #    channel.close()
                #if connection.is_open:
                #    connection.close()
                logging.error('----------------- restarting connection and channel -----------------')
                time.sleep(3)


    def get_current_arbitrage_opportunities(self):
        last_file_name = json.loads(open('/home/ubuntu/arbitrage_opportunities/' + self.arbitrage_type + '/' + 'info.json', 'r', encoding='UTF-8').read())['last_file_name']
        if os.path.isfile('/home/ubuntu/arbitrage_opportunities/' + self.arbitrage_type + '/' + last_file_name):
            return json.loads(open('/home/ubuntu/arbitrage_opportunities/' + self.arbitrage_type + '/' + last_file_name, 'r', encoding='UTF-8').read())

    def update_order_books_file(self):
        file_name = str(int(time.time() * 1e3)) + '.json'
            
        f = open( '/home/ubuntu/arbitrage_opportunities/' + self.arbitrage_type + '/' + 'info.json', 'w+', encoding='UTF-8')
        f.write( json.dumps({'last_file_name': file_name}) )
        f.close()     
            
        f = open( '/home/ubuntu/arbitrage_opportunities/' + self.arbitrage_type + '/' + file_name, 'w+', encoding='UTF-8')
        f.write( json.dumps(self.arbitrage_opportunities) )
        f.close() 

    def check_order_books(self):
        while True:
            logging.info('----------------- start check_order_books -----------------')
            logging.info('------------------------ %s %s', self.arbitrage_opportunities, len(self.arbitrage_opportunities))
            update = False
            for key in list(self.arbitrage_opportunities):
                if self.arbitrage_opportunities[key]['last_time'] < int(time.time() * 1e3) - (40 * 1e3):
                    update = True
                    del self.arbitrage_opportunities[key]
            
            if update:
                self.update_order_books_file()
            logging.info('----------------- end check_order_books -----------------')
            time.sleep(10)

    def callback(self, ch, method, properties, body):
        body_json = json.loads(body)
        order_book_time = body_json['time']
        exchange = body_json['exchange']
        base_asset = body_json['base_asset']
        quote_asset = body_json['quote_asset']
        data = body_json['data']
        match self.arbitrage_type:
            case 'simple':
                self.check_arbitrage_simple(
                    order_book_time=order_book_time,
                    exchange=exchange,
                    base_asset=base_asset,
                    quote_asset=quote_asset,
                    data=data
                )
            case 'triple':
                self.check_arbitrage_triple(
                    order_book_time=order_book_time,
                    exchange=exchange,
                    base_asset=base_asset,
                    quote_asset=quote_asset,
                    data=data
                )
                
    def check_arbitrage_simple(self, order_book_time: int, exchange: str, base_asset: str, quote_asset: str, data: dict):
        pair: str = base_asset + '-' + quote_asset   
        
        if pair not in self.order_books:
            self.order_books[pair] = {}     
        if data is not None and len(data) > 0:
            data['time'] = order_book_time
            self.order_books[pair][exchange] = data
            
        if len(self.order_books[pair]) == 1:
            return
            
        exchange_groups = list(itertools.combinations(self.order_books[pair].keys(), 2))
        #logging.info('exchange_groups %s', exchange_groups)
        for exchange_group in exchange_groups:
            exchange_combinations = [
                {'exchange_1': exchange_group[0], 'exchange_2': exchange_group[1]},
                {'exchange_1': exchange_group[1], 'exchange_2': exchange_group[0]}
            ]
            #logging.info('exchange_combinations %s', exchange_combinations)                
            for exchange_combination in exchange_combinations:
                exchange_1 = exchange_combination['exchange_1']
                exchange_2 = exchange_combination['exchange_2']
                if exchange_1 not in self.order_books[pair] or len(self.order_books[pair][exchange_1]["asks"]) == 0 or self.order_books[pair][exchange_1]["time"] < int(time.time() * 1e3) - (60 * 1e3):
                    continue
                if exchange_2 not in self.order_books[pair] or len(self.order_books[pair][exchange_2]["bids"]) == 0 or self.order_books[pair][exchange_2]["time"] < int(time.time() * 1e3) - (60 * 1e3):
                    continue
                #logging.info('comparing %s with %s in pair %s', exchange_1, exchange_2, pair)
                #logging.info('first %s ASK %s', exchange_1, self.order_books[pair][exchange_1]["asks"][0])
                #logging.info('first %s BID %s', exchange_2, self.order_books[pair][exchange_2]["bids"][0])
                    
                first_ask_price = float(self.order_books[pair][exchange_1]['asks'][0][0])
                first_bid_price = float(self.order_books[pair][exchange_2]['bids'][0][0])
                depth = float(self.order_books[pair][exchange_1]['asks'][0][1])
                if float(self.order_books[pair][exchange_2]['bids'][0][1]) < depth:
                    depth = float(self.order_books[pair][exchange_2]['bids'][0][1])
                arb_opportunity = first_bid_price - first_ask_price
                profitability_percentage = (arb_opportunity * 100 / first_ask_price) - (self.exchanges_info[exchange_1][pair]['buy_fee_percentage'] + self.exchanges_info[exchange_2][pair]['sell_fee_percentage'])
                profitability_amount = profitability_percentage * first_ask_price * depth / 100
                if profitability_percentage < self.min_profitability_percentage:
                    #logging.info('----------------------------------- simple min profitability is not reached %s %s', profitability_percentage, self.min_profitability_percentage)
                    print('----------------------------------- simple min profitability is not reached', profitability_percentage, self.min_profitability_percentage)
                    continue
                current_time = int(time.time() * 1e3)
                key = exchange_1 + '__' + exchange_2 + '__' + pair
                if key not in self.arbitrage_opportunities:
                    self.arbitrage_opportunities[key] = {
                        'init_time': current_time,
                        'last_time': current_time,
                        'profitability_percentage': profitability_percentage,
                        'depth': depth,
                        'profitability_amount': profitability_amount,
                        'profitability_asset': quote_asset,
                        'exchange_1_asks': self.order_books[pair][exchange_1]["asks"],
                        'exchange_2_bids': self.order_books[pair][exchange_2]["bids"],
                    }
                    if profitability_percentage > 1:
                        logging.info('----------------------------------- new opportunity %s %s', key, self.arbitrage_opportunities[key])
                    #self.update_order_books_file()  
                if profitability_percentage > self.arbitrage_opportunities[key]['profitability_percentage']:
                    self.arbitrage_opportunities[key]['profitability_percentage'] = profitability_percentage
                    self.arbitrage_opportunities[key]['depth'] = depth      
                    self.arbitrage_opportunities[key]['profitability_amount'] = profitability_amount             
                self.arbitrage_opportunities[key]['last_time'] = current_time

    def check_arbitrage_triple(self, order_book_time: int, exchange: str, base_asset: str, quote_asset: str, data: dict):
        pair: str = base_asset + '-' + quote_asset   
        base_asset_final = None
        for pivot_asset in ['BTC', 'ETH']:
            if base_asset != pivot_asset:
                base_asset_final = base_asset
            if pair not in self.order_books:
                self.order_books[pair] = {}     
            if data is not None and len(data) > 0:
                data['time'] = order_book_time
                self.order_books[pair][exchange] = data
                
            if base_asset_final is None:
                return
                        
            pair_1 = base_asset_final + '-' + pivot_asset
            pair_2 = pivot_asset + '-' + quote_asset
            pair_3 = base_asset_final + '-' + quote_asset
            if pair_1 not in self.order_books or pair_2 not in self.order_books or pair_3 not in self.order_books:
                return
            if exchange not in self.order_books[pair_1] or len(self.order_books[pair_1][exchange]["asks"]) == 0 or len(self.order_books[pair_1][exchange]["bids"]) == 0 or self.order_books[pair_1][exchange]["time"] < int(time.time() * 1e3) - (60 * 1e3):
                return
            if exchange not in self.order_books[pair_2] or len(self.order_books[pair_2][exchange]["asks"]) == 0 or len(self.order_books[pair_2][exchange]["bids"]) == 0 or self.order_books[pair_2][exchange]["time"] < int(time.time() * 1e3) - (60 * 1e3):
                return
            if exchange not in self.order_books[pair_3] or len(self.order_books[pair_3][exchange]["asks"]) == 0 or len(self.order_books[pair_3][exchange]["bids"]) == 0 or self.order_books[pair_3][exchange]["time"] < int(time.time() * 1e3) - (60 * 1e3):
                return
                    
            variations = [
                {
                    'id': 'SELL-SELL-BUY',
                    'values': [
                        {
                            'pair': base_asset_final + '-' + pivot_asset,
                            'tradeSide': TradeSide.SELL
                        },
                        {
                            'pair': pivot_asset + '-' + quote_asset,
                            'tradeSide': TradeSide.SELL
                        },
                        {
                            'pair': base_asset_final + '-' + quote_asset,
                            'tradeSide': TradeSide.BUY
                        }
                    ],
                },
                {
                    'id': 'SELL-BUY-BUY',
                    'values': [
                        {
                            'pair': base_asset_final + '-' + quote_asset,
                            'tradeSide': TradeSide.SELL
                        },
                        {
                            'pair': pivot_asset + '-' + quote_asset,
                            'tradeSide': TradeSide.BUY
                        },
                        {
                            'pair': base_asset_final + '-' + pivot_asset,
                            'tradeSide': TradeSide.BUY
                        }
                    ],
                },
                {
                    'id': 'BUY-SELL-SELL',
                    'values': [
                        {
                            'pair': base_asset_final + '-' + quote_asset,
                            'tradeSide': TradeSide.BUY
                        },
                        {
                            'pair': base_asset_final + '-' + pivot_asset,
                            'tradeSide': TradeSide.SELL
                        },
                        {
                            'pair': pivot_asset + '-' + quote_asset,
                            'tradeSide': TradeSide.SELL
                        }
                    ],
                },
                {
                    'id': 'BUY-BUY-SELL',
                    'values': [
                        {
                            'pair': pivot_asset + '-' + quote_asset,
                            'tradeSide': TradeSide.BUY
                        },
                        {
                            'pair': base_asset_final + '-' + pivot_asset,
                            'tradeSide': TradeSide.BUY
                        },
                        {
                            'pair': base_asset_final + '-' + quote_asset,
                            'tradeSide': TradeSide.SELL
                        }
                    ],
                }
            ]        
                                            
            for variation in variations:
                        
                if variation['id'] == 'BUY-BUY-SELL':
                    continue
                                                        
                depth = float(self.order_books[variation['values'][0]['pair']][exchange]['bids' if variation['values'][0]['tradeSide'] == TradeSide.SELL else 'asks'][0][1])
                                
                price_1 = float(self.order_books[variation['values'][0]['pair']][exchange]['bids' if variation['values'][0]['tradeSide'] == TradeSide.SELL else 'asks'][0][0])
                price_2 = float(self.order_books[variation['values'][1]['pair']][exchange]['bids' if variation['values'][1]['tradeSide'] == TradeSide.SELL else 'asks'][0][0])
                price_3 = float(self.order_books[variation['values'][2]['pair']][exchange]['bids' if variation['values'][2]['tradeSide'] == TradeSide.SELL else 'asks'][0][0])
                                                        
                pair_1 = variation['values'][0]['pair']
                pair_2 = variation['values'][1]['pair']
                pair_3 = variation['values'][2]['pair']
                
                '''
                logging.info('first %s %s (%s) %s - %s (%s) %s - %s (%s) %s', 
                    exchange, 
                    variation['values'][0]['tradeSide'],
                    variation['values'][0]['pair'],
                    price_1, 
                    variation['values'][1]['tradeSide'],
                    variation['values'][1]['pair'],
                    price_2, 
                    variation['values'][2]['tradeSide'],
                    variation['values'][2]['pair'],
                    price_3
                )
                '''
                                                                                    
                profitability_percentage = 0
                bid_avg_price = None        
                ask_avg_price = None
                        
                if variation['id'] == 'SELL-SELL-BUY':
                    bid_avg_price = price_1 * price_2
                    ask_avg_price = price_3
                    arb_opportunity = bid_avg_price - ask_avg_price
                    profitability_percentage = (arb_opportunity * 100 / ask_avg_price) - (self.exchanges_info[exchange][pair_1]['sell_fee_percentage'] + self.exchanges_info[exchange][pair_2]['sell_fee_percentage'] + self.exchanges_info[exchange][pair_3]['buy_fee_percentage'])
                    profitability_amount = profitability_percentage * depth / 100
                    profitability_asset = base_asset_final
                elif variation['id'] == 'SELL-BUY-BUY':
                    bid_avg_price = price_1
                    ask_avg_price = price_2 * price_3
                    arb_opportunity = bid_avg_price - ask_avg_price
                    profitability_percentage = (arb_opportunity * 100 / ask_avg_price) - (self.exchanges_info[exchange][pair_1]['sell_fee_percentage'] + self.exchanges_info[exchange][pair_2]['buy_fee_percentage'] + self.exchanges_info[exchange][pair_3]['buy_fee_percentage'])
                    profitability_amount = profitability_percentage * depth / 100
                    profitability_asset = base_asset_final
                elif variation['id'] == 'BUY-SELL-SELL':
                    bid_avg_price = price_2 * price_3
                    ask_avg_price = price_1
                    arb_opportunity = bid_avg_price - ask_avg_price
                    profitability_percentage = (arb_opportunity * 100 / ask_avg_price) - (self.exchanges_info[exchange][pair_1]['buy_fee_percentage'] + self.exchanges_info[exchange][pair_2]['sell_fee_percentage'] + self.exchanges_info[exchange][pair_3]['sell_fee_percentage'])
                    profitability_amount = profitability_percentage * ask_avg_price * depth / 100
                    profitability_asset = quote_asset
                elif variation['id'] == 'BUY-BUY-SELL':
                    bid_avg_price = price_3
                    ask_avg_price = price_1 * price_2
                    arb_opportunity = bid_avg_price - ask_avg_price
                    profitability_percentage = (arb_opportunity * 100 / ask_avg_price) - (self.exchanges_info[exchange][pair_1]['buy_fee_percentage'] + self.exchanges_info[exchange][pair_2]['buy_fee_percentage'] + self.exchanges_info[exchange][pair_3]['sell_fee_percentage'])
                    profitability_amount = profitability_percentage * ask_avg_price * depth / 100
                    profitability_asset = quote_asset
                
                if profitability_percentage < self.min_profitability_percentage:
                    logging.info('----------------------------------- triple min profitability is not reached %s - %s %s %s %s -> %s %s', 
                        variation['id'], 
                        exchange, 
                        pair_1, 
                        pair_2, 
                        pair_3, 
                        profitability_percentage, 
                        self.min_profitability_percentage
                    )
                    continue     
                                
                current_time = int(time.time() * 1e3)
                key = exchange + '__' + pair_1 + '__' + pair_2 + '__' + pair_3
                if key not in self.arbitrage_opportunities:
                    self.arbitrage_opportunities[key] = {
                        'init_time': current_time,
                        'last_time': current_time,
                        'profitability_percentage': profitability_percentage,
                        'depth': depth,
                        'profitability_amount': profitability_amount,
                        'profitability_asset': profitability_asset,
                        'variation': variation['id']
                    }
                    self.update_order_books_file()  
                if profitability_percentage > self.arbitrage_opportunities[key]['profitability_percentage']:
                    self.arbitrage_opportunities[key]['profitability_percentage'] = profitability_percentage
                    self.arbitrage_opportunities[key]['depth'] = depth      
                    self.arbitrage_opportunities[key]['profitability_amount'] = profitability_amount             
                self.arbitrage_opportunities[key]['last_time'] = current_time
                                

arbitrage_opportunities = ArbitrageOpportunities(arbitrage_type=sys.argv[1])
arbitrage_opportunities.run()
