import time
import json
import os
from damexCommons.tools.dbs import get_exchange_db
from damexCommons.tools.utils import EXCHANGE_FOLDER
from damexCommons.base import Order, OrderSide

exchange_db = get_exchange_db(db_connection='exchange')

async def get_order_book_price(base_asset: str, quote_asset: str, currency: str, side: str, amount: float):
    order_book = await exchange_db.get_order_book_db(base_asset=base_asset, quote_asset=quote_asset, size=100)
    if len(order_book['bids']) == 0 and len(order_book['asks']) == 0 :
        main_price = await get_main_price(base_asset=base_asset, quote_asset=quote_asset)
        if side == 'sell':
            return {'price': main_price * 0.95, 'amount': 0} 
        elif side == 'buy':
            return {'price': main_price * 1.05, 'amount': 0} 
    if len(order_book['bids']) == 0 and len(order_book['asks']) > 0 and side == 'sell':
        return {'price': order_book['asks'][0][0] * 0.95, 'amount': 0}
    if len(order_book['asks']) == 0 and len(order_book['bids']) > 0 and side == 'buy':
        return {'price': order_book['bids'][0][0] * 1.05, 'amount': 0}
    
    amount_left = float(amount)
    amount_by_price_sum = 0
    for o in  order_book['bids' if side == 'sell' else 'asks']:  
        price_ob = float(o[0])
        amount_ob = float(o[1])
        var = None
        if base_asset == currency:
            var = amount_ob
        elif quote_asset == currency:
            var = float(price_ob * amount_ob)
        else:
            return None
        if var >= amount_left:
            amount_by_price_sum += price_ob * amount_left
            amount_left = 0
            break 
        else:
            amount_by_price_sum += price_ob * var
            amount_left = amount_left - var
            
    amount_new = float(amount) - amount_left
    if amount_new == 0:
        print('-------------7')
        return {'price': None, 'amount': 0}   
    price_new = amount_by_price_sum / amount_new
    if side == 'sell' and len(order_book['asks']) > 0:
        ask_lowest_price = float(order_book['asks'][0][0])
        if price_new > ask_lowest_price:
            price_new = ask_lowest_price
    print('-------------8')
    return {'price': price_new, 'amount': amount_new}   


async def match_trade_order(exchange: str, base_asset: str, quote_asset: str, price: float, amount: float, trade_side: str):
    sides = {1: False, 2: False}
    open_orders: list[Order] = await exchange_db.fetch_orders_last_12_minutes_db(base_asset=base_asset, quote_asset=quote_asset, exchanges=[exchange], price=price, amount=amount, by_type=False)
    for open_order in  open_orders:
        sides[open_order.side.value] = True
    if sides == {1: False, 2: False}:
        open_orders = await exchange_db.fetch_orders_last_12_minutes_db(base_asset=base_asset, quote_asset=quote_asset, exchanges=[exchange], price=price, by_type=False)
        if len(open_orders) > 0:
            if open_orders[0].amount > amount:
                if len(open_orders) == 1:
                    if (trade_side == 'BUY' and open_orders[0].side == OrderSide.ASK) or (trade_side == 'SELL' and open_orders[0].side == OrderSide.BID):
                        exetutor = 'maker__partially_filled'
                    else:
                        exetutor = 'taker__partially_filled'
                    return {'executor': exetutor, 'bot_id': open_orders[0].bot_id, 'strategy': open_orders[0].strategy_id}
                else:
                    return {'executor': 'maker__taker__partially_filled', 'bot_id': open_orders[0].bot_id, 'strategy': open_orders[0].strategy_id}
            else:
                print('problem--------------------')
        else:
            return {'executor': 'other'}        
    elif sides == {1: True, 2: False} or sides == {1: False, 2: True}:
        if (trade_side == 'BUY' and sides == {1: True, 2: False})or (trade_side == 'SELL' and sides == {1: False, 2: True}):
            executor = 'maker'
        else:
            executor = 'taker'
        return {'executor': executor, 'bot_id': open_orders[0].bot_id, 'strategy': open_orders[0].strategy_id}
    elif sides == {1: True, 2: True}:
        return {'executor': 'maker__taker', 'bot_id': open_orders[0].bot_id, 'strategy': open_orders[0].strategy_id}
    
async def get_main_price(base_asset: str, quote_asset: str):
    market = base_asset + '-' + quote_asset
    main_price_parameters = await exchange_db.get_main_price_parameters_db(base_asset=base_asset, quote_asset=quote_asset, include_active_exchanges=True)
    if main_price_parameters is None:
        return 0
            
    match main_price_parameters['main_price_type']:
        case 2:
            return await get_last_price(base_asset, quote_asset, main_price_parameters['price_floor'], main_price_parameters['price_ceiling'])
        case 7:   
            period_time = int(main_price_parameters['weighted_price_limit_time']) * 1000
            max_tickers_per_source = int(main_price_parameters['weighted_price_max_tickers_per_source'])
            exponential_factor = int(main_price_parameters['weighted_price_exponential_factor'])
            active_exchanges = main_price_parameters['active_exchanges']
            price_floor = main_price_parameters['price_floor']
            price_ceiling = main_price_parameters['price_ceiling']
            previous_timestamp = int(time.time() * 1000) - period_time
            all_trades = []
            ## APP TIDEX AND BITMART LAST PRICE
            sources = ['APP']
            sources.extend(active_exchanges)
            for source in sources:   
                info_trades_file = '%s/%s/%s/%s/%s' % (EXCHANGE_FOLDER, source, 'trades', market, '/info.json')
                if not os.path.exists(info_trades_file):
                    continue
                try: 
                    info = json.loads(open(info_trades_file, 'r', encoding='UTF-8').read())
                except Exception as e:  
                    print('exception', e)
                    continue
                last_trades = info['last_trades']
                selected_trades = []
                for last_trade in last_trades:
                    if previous_timestamp > int(last_trade['timestamp']):
                        continue
                    selected_trades.append(last_trade)
                selected_trades = selected_trades[-max_tickers_per_source:]
                all_trades.extend(selected_trades)
                all_trades.sort(key=lambda x: x['timestamp'])
            if len(all_trades) == 0:
                return await get_last_price(base_asset, quote_asset, main_price_parameters['price_floor'], main_price_parameters['price_ceiling'])
            total_specific_volume = 0
            total_last_price_by_specific_volume = 0
            for selected_trade in all_trades:                     
                if (not 'price' in selected_trade) or (not 'amount' in selected_trade):           
                    continue      
                total_last_price_by_specific_volume += round(float(selected_trade['price']), 6) * pow(float(selected_trade['amount']), exponential_factor)
                total_specific_volume += pow(float(selected_trade['amount']), exponential_factor)
            if total_specific_volume == 0:
                return 0
            final_price = float(total_last_price_by_specific_volume / total_specific_volume)
            if final_price < price_floor:
                final_price = price_floor
            elif final_price > price_ceiling:
                final_price = price_ceiling
            return round(final_price, 5 if market == 'DAMEX-USDT' else 6 if market == 'HOT-USDT' else 2)
    return 0

async def get_last_price(base_asset: str, quote_asset: str, price_floor: float, price_ceiling: float):
    market = base_asset + '-' + quote_asset
    last_trade_timestamp = None
    final_price = None
    sources: dict = {
        'DAMEX-USDT': ['APP', 'ascendex', 'tidex', 'bitmart', 'coinstore', 'mexc'],
        'HOT-USDT': ['binance'],
        'SOL-USDC': ['binance']
    }
    for source in sources[market]:   
        info_trades_file = '%s/%s/%s/%s/%s' % (EXCHANGE_FOLDER, source, 'trades', market, 'info.json')
        if not os.path.exists(info_trades_file):
            continue
        i = 0
        while i < 3:
            i += 1
            info = None
            try:
                f = open(info_trades_file, 'r', encoding='UTF-8')
                info = json.loads(f.read())
            except Exception as e:
                print('e', e)
                time.sleep(100)
                print('retrying--------------', i)
            finally:
                f.close()
            if info is not None:
                break
        last_trades = info['last_trades']
        if len(last_trades) == 0:
            continue
        new_last_trade_timestamp = int(last_trades[len(last_trades) - 1]['timestamp'])
        if last_trade_timestamp is None or new_last_trade_timestamp > last_trade_timestamp:
            final_price = float(last_trades[len(last_trades) - 1]['price'])
            last_trade_timestamp = new_last_trade_timestamp
    
    if final_price < price_floor:
        final_price = price_floor
    elif final_price > price_ceiling:
        final_price = price_ceiling

    return round(final_price, 5 if market == 'DAMEX-USDT' else 6 if market == 'HOT-USDT' else 2)
