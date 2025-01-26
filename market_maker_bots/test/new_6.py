import os
import sys
import asyncio
import time
import datetime
import logging
from typing import Dict, Callable, Any, List, NamedTuple, Optional
from threading import Thread, Event
import itertools
import atexit
sys.path.append(os.getcwd())
from damexCommons.tools.connections import get_commons


class ArbitrageBusiness:
    
    def __init__(self, id: int, base_asset: str, quote_asset: str, exchanges: list[str], min_depth: float, max_depth: float):
        self.id = id
        self.base_asset = base_asset
        self.quote_asset = quote_asset
        self.exchanges = exchanges
        self.commons = {}
        self.order_books = {}
        self.min_depth = min_depth
        self.max_depth = max_depth
        self.trade_time = None
        self.trades = {}
        self.stop_ws = {}

    async def execute(self, exchange: str, base_asset: str, quote_asset: str, name: str, attributes: tuple) -> None:
        key: str = exchange + '__' + base_asset + '-' + quote_asset
        api = exchange + '__main'
        if key not in self.commons:
            self.commons[key] = get_commons(base_asset=base_asset, quote_asset=quote_asset, exchange_or_connector=exchange, api_or_wallet=api)
        #att = dir(self.commons[key])
        #print('--------------------------att', att)
        #print('--------------------------self.commons', self.commons)
        #return self.commons[key]
        await getattr(self.commons[key], name)(*attributes)
    
    async def execution(self, exchange: str, base_asset: str, quote_asset: str, data: dict) -> None:
        if len(data) == 0:
            return
        print('data', data)
        return
        if data is not None and len(data) > 0:
            self.order_books[exchange] = data
            #print('-----------------------', self.order_books)

        if len(self.order_books) == len(self.exchanges):
            
            expenses_percentage = 0.02
            min_profitability = 0.05
            
            exchange_groups = list(itertools.combinations(self.exchanges, 2))
            print('exchange_groups', exchange_groups)
            for exchange_group in exchange_groups:
                exchange_combinations = [
                    {'exchange_1': exchange_group[0], 'exchange_2': exchange_group[1]},
                    {'exchange_1': exchange_group[1], 'exchange_2': exchange_group[0]}
                ]
                print('exchange_combinations', exchange_combinations)
                for exchange_combination in exchange_combinations:
                    exchange_1 = exchange_combination['exchange_1']
                    exchange_2 = exchange_combination['exchange_2']
                    print(f'comparing {exchange_1} with {exchange_2} in pair {self.base_asset}-{self.quote_asset}')
                    print(f'first {exchange_1} ASK {self.order_books[exchange_1]["asks"][0]}')
                    print(f'first {exchange_2} BID {self.order_books[exchange_2]["bids"][0]}')
                    bid_levels = 0
                    total_bid_amount = 0
                    bids_price_per_amount_sum = 0
                    first_ask_price = float(self.order_books[exchange_1]['asks'][0][0])
                    for bid in self.order_books[exchange_2]['bids']:
                        bid_price = float(bid[0])
                        bid_amount = float(bid[1])
                        if first_ask_price * (1 + (expenses_percentage / 100)) < bid_price:
                            bids_price_per_amount_sum += bid_price * bid_amount
                            total_bid_amount += bid_amount
                            if bids_price_per_amount_sum > self.max_depth:
                                bids_price_per_amount_sum -= bid_price * bid_amount
                                total_bid_amount -= bid_amount
                                bids_price_per_amount_sum += bid_price * (self.max_depth - total_bid_amount)
                                total_bid_amount += (self.max_depth - total_bid_amount)
                            bid_levels += 1
                            if total_bid_amount >= self.max_depth:
                                break
                        else:
                            break
                    ask_levels = 0
                    total_ask_amount = 0
                    asks_price_per_amount_sum = 0
                    first_bid_price = float(self.order_books[exchange_2]['bids'][0][0])
                    for ask in self.order_books[exchange_1]['asks']:
                        ask_price = float(ask[0])
                        ask_amount = float(ask[1])
                        if first_bid_price > ask_price * (1 + (expenses_percentage / 100)):
                            asks_price_per_amount_sum += ask_price * ask_amount
                            total_ask_amount += ask_amount
                            if asks_price_per_amount_sum > self.max_depth:
                                asks_price_per_amount_sum -= ask_price * ask_amount
                                total_ask_amount -= ask_amount
                                asks_price_per_amount_sum += ask_price * (self.max_depth - total_ask_amount)
                                total_ask_amount += (self.max_depth - total_ask_amount)
                            ask_levels += 1
                            if total_ask_amount >= self.max_depth:
                                break
                    depth = total_bid_amount
                    levels = bid_levels
                    if total_ask_amount < depth:
                        depth = total_ask_amount
                        levels = ask_levels
                    if depth < self.min_depth:
                        print('-----------------------------------1', f'min depth is not reached')
                        continue
                    ask_avg_price = asks_price_per_amount_sum / total_ask_amount
                    bid_avg_price = bids_price_per_amount_sum / total_bid_amount
                    arb_opportunity = bid_avg_price - ask_avg_price      
                    profitability = (arb_opportunity * 100 / ask_avg_price) - expenses_percentage
                    if profitability < min_profitability:
                        print('-----------------------------------2', f'min profitability is not reached')
                        continue
                    if balances[exchange_1][self.quote_asset]['available'] < depth * ask_avg_price * 0.95:
                        print('-----------------------------------3', f'not enough balance to buy in exchange_1', balances[exchange_1][self.quote_asset]['available'] / ask_avg_price, depth * 0.95)
                        continue
                    if balances[exchange_2][self.base_asset]['available'] < depth * 0.95:
                        print('-----------------------------------4', f'not enough balance to sell in exchange_2', balances[exchange_2][self.base_asset]['available'], depth * 0.95)
                        continue
                    profit = round(float(depth * arb_opportunity * (1 - expenses_percentage / 100)), 2)                    
                    if self.trade_time is None or int(time.time() * 1000) - (5 * 1000) >= self.trade_time:
                        self.trade_time = int(time.time() * 1000)
                        data = {
                            'base_asset': self.base_asset,
                            'quote_asset': self.quote_asset,
                            'exchange_1': exchange_1,
                            'exchange_2': exchange_2,
                            'price_buy_1': ask_avg_price,
                            'price_sell_2': bid_avg_price,
                            'depth': depth,
                            'levels': levels,
                            'arb_opportunity': arb_opportunity,
                            'profitability': profitability,
                            'profit': profit,
                        }
                        trade_1 = {
                            'base_asset': self.base_asset,
                            'quote_asset': self.quote_asset,
                            'exchange': exchange_1,
                            'price': ask_avg_price,
                            'amount': depth,
                            'amount_quote': depth * ask_avg_price,
                            'side': 'BUY'
                        }
                        trade_2 = {
                            'base_asset': self.base_asset,
                            'quote_asset': self.quote_asset,
                            'exchange': exchange_2,
                            'price': bid_avg_price,
                            'amount': depth,
                            'amount_quote': depth * bid_avg_price,
                            'side': 'SELL'
                        }
                        
                        balances[exchange_1][self.quote_asset]['available'] -= ask_avg_price * depth
                        balances[exchange_1][self.quote_asset]['total'] -= ask_avg_price * depth
                        balances[exchange_1][self.base_asset]['available'] += depth
                        balances[exchange_1][self.base_asset]['total'] += depth
                        
                        balances[exchange_2][self.quote_asset]['available'] += bid_avg_price * depth
                        balances[exchange_2][self.quote_asset]['total'] += bid_avg_price * depth
                        balances[exchange_2][self.base_asset]['available'] -= depth
                        balances[exchange_2][self.base_asset]['total'] -= depth
                        
                        self.trades[self.trade_time] = [trade_1, trade_2]
                        
                        print('-------------------TRADE-------------------')
                        print('--info--', data)
                        print('--trade_1--', trade_1)
                        print('--trade_2--', trade_2)
                        print('--trades count--', len(self.trades))
                        print('--new balances--', balances)
                        print('--USDT--', balances[exchange_1]['USDT']['total'] + balances[exchange_2]['USDT']['total'])
                        print('-------------------TRADE-------------------')

                    break

    def run(self):
        t_0 = Thread(target=self.main_thread)
        t_0.start()    

    def main_thread(self) -> None:
        started = False
        while True:
            try:
                if not started:
                    asyncio.run(self.start())
                    started = True
                time.sleep(3)
            except Exception as e:
                print(f'main thread {e}')
                time.sleep(1)

    async def start(self) -> None:
        for exchange in self.exchanges:
            thread = Thread(target=self.order_book_thread, args=(exchange,))
            thread.start()   

    def order_book_thread(self, exchange: str) -> None:
        id = exchange + '__' + self.base_asset + '-' + self.quote_asset   
        self.stop_ws[id] = False        
        asyncio.run(self.execute(exchange=exchange, base_asset=self.base_asset, quote_asset=self.quote_asset, name='run_wss', attributes=(self.base_asset, self.quote_asset, 'order_book', self.stop_ws, self.execution,)))
           
balances = {
    'tidex': {
        'USDT': {
            'available': 4800,
            'total': 4800
        },
        'ETH': {
            'available': 0,
            'total': 0
        },
        'SOL': {
            'available': 0,
            'total': 0
        },
        'ADA': {
            'available': 0,
            'total': 0
        },
        'BNB': {
            'available': 0,
            'total': 0
        },
        'DOGE': {
            'available': 0,
            'total': 0
        },
    },
    'mexc': {
        'USDT': {
            'available': 100,
            'total': 100
        },
        'ETH': {
            'available': 1,
            'total': 1
        },
        'SOL': {
            'available': 10,
            'total': 10
        },
        'ADA': {
            'available': 10000,
            'total': 10000
        },
        'BNB': {
            'available': 10,
            'total': 10
        },
        'DOGE': {
            'available': 30000,
            'total': 30000
        },
    },
    'bitmart': {
        'USDT': {
            'available': 100,
            'total': 100
        },
        'ETH': {
            'available': 1,
            'total': 1
        },
        'SOL': {
            'available': 10,
            'total': 10
        },
        'ADA': {
            'available': 10000,
            'total': 10000
        },
        'BNB': {
            'available': 10,
            'total': 10
        },
        'DOGE': {
            'available': 30000,
            'total': 30000
        },
    }
}        


start_time = int(time.time() * 1000)
exchanges = ['mexc', 'tidex', 'bitmart']
exchanges = ['bitfinex']
quote_asset = 'USD'
base_assets = ['DOGE', 'SOL', 'ADA']
base_assets = ['BTC']
arbitrage_businesses: list[ArbitrageBusiness] = []

DEPTHS = {
    'BTC': {
        'min_depth': 0.01,
        'max_depth': 0.04
    },
    'ETH': {
        'min_depth': 0.1,
        'max_depth': 0.4
    },
    'SOL': {
        'min_depth': 1,
        'max_depth': 4
    },
    'ADA': {
        'min_depth': 1000,
        'max_depth': 4000
    },
    'BNB': {
        'min_depth': 1,
        'max_depth': 4
    },
    'DOGE': {
        'min_depth': 3000,
        'max_depth': 12000
    },
}

id = 1
for base_asset in base_assets:
    arbitrage_business = ArbitrageBusiness(id=id, base_asset=base_asset, quote_asset=quote_asset, exchanges=exchanges, min_depth=DEPTHS[base_asset]['min_depth'], max_depth=DEPTHS[base_asset]['max_depth'])
    arbitrage_businesses.append(arbitrage_business)
    id += 1
    arbitrage_business.run()


def exit_handler():
    trades_count = 0
    for arbitrage_business in arbitrage_businesses:
        trades_count += len(arbitrage_business.trades)
        print('----------------------------', f'Arbitrage Business {arbitrage_business.id}', '----------------------------')
        print('Base asset', arbitrage_business.base_asset)
        print('Trades count', len(arbitrage_business.trades))
        print('Trades', arbitrage_business.trades)
    print('----------------------------', 'TOTAL', '----------------------------')
    usdt = 0
    for exchange in balances:
        usdt += balances[exchange]['USDT']['total']
    print('Running time', datetime.timedelta(seconds=int((int(time.time() * 1000) - start_time) / 1000)))
    print('Balances', balances)
    print('Trades count', trades_count)
    print('Exchanges', exchanges)
    print('USDT', round(usdt, 2)) 
    
atexit.register(exit_handler)
