import os
import sys
import asyncio
sys.path.append(os.getcwd())
from damexCommons.base import Trade, TradeSide
from damexCommons.tools.dbs import get_bot_db

def calculate_total_balance(balance: dict):
    total_balance_final = {}
    for exchange in balance:
        for asset in balance[exchange]:
            if asset not in total_balance_final:
                total_balance_final[asset] = 0
            total_balance_final[asset] += balance[exchange][asset]['total']
    return total_balance_final   

BALANCES_INITIAL = {
    'tidex': {'USDT': {'available': 4800, 'total': 4800}, 'ETH': {'available': 0, 'total': 0}, 'SOL': {'available': 0.0, 'total': 0.0}, 'ADA': {'available': 0.0, 'total': 0.0}, 'BNB': {'available': 0, 'total': 0}, 'DOGE': {'available': 0, 'total': 0}}, 
    'mexc': {'USDT': {'available': 100, 'total': 100}, 'ETH': {'available': 1, 'total': 1}, 'SOL': {'available': 10.0, 'total': 10.0}, 'ADA': {'available': 10000.0, 'total': 10000.0}, 'BNB': {'available': 10.0, 'total': 10.0}, 'DOGE': {'available': 30000.0, 'total': 30000.0}}, 
    'bitmart': {'USDT': {'available': 100, 'total': 100}, 'ETH': {'available': 1, 'total': 1}, 'SOL': {'available': 10.0, 'total': 10.0}, 'ADA': {'available': 10000.0, 'total': 10000.0}, 'BNB': {'available': 10.0, 'total': 10.0}, 'DOGE': {'available': 30000.0, 'total': 30000.0}}, 
    'coinstore': {'USDT': {'available': 4800, 'total': 4800}, 'ETH': {'available': 0, 'total': 0}, 'SOL': {'available': 0.0, 'total': 0.0}, 'ADA': {'available': 0.0, 'total': 0.0}, 'BNB': {'available': 0, 'total': 0}, 'DOGE': {'available': 0, 'total': 0}}, 
    'ascendex': {'USDT': {'available': 100, 'total': 100}, 'ETH': {'available': 1, 'total': 1}, 'SOL': {'available': 10.0, 'total': 10.0}, 'ADA': {'available': 10000.0, 'total': 10000.0}, 'BNB': {'available': 10.0, 'total': 10.0}, 'DOGE': {'available': 30000.0, 'total': 30000.0}}, 
    'binance': {'USDT': {'available': 100, 'total': 100}, 'ETH': {'available': 1, 'total': 1}, 'SOL': {'available': 10.0, 'total': 10.0}, 'ADA': {'available': 10000.0, 'total': 10000.0}, 'BNB': {'available': 10.0, 'total': 10.0}, 'DOGE': {'available': 30000.0, 'total': 30000.0}},
}

BALANCES_FINAL = {
    'tidex': {'USDT': {'available': -42.15100020099999, 'total': -42.15100020099999}, 'ETH': {'available': 0, 'total': 0}, 'SOL': {'available': 0.0, 'total': 0.0}, 'ADA': {'available': 0.0, 'total': 0.0}, 'BNB': {'available': 0, 'total': 0}, 'DOGE': {'available': 0, 'total': 0}}, 
    'mexc': {'USDT': {'available': 2166.01183, 'total': 2166.01183}, 'ETH': {'available': 1, 'total': 1}, 'SOL': {'available': 2.0, 'total': 2.0}, 'ADA': {'available': 930.0, 'total': 930.0}, 'BNB': {'available': 2.0, 'total': 2.0}, 'DOGE': {'available': 2795.0, 'total': 2795.0}}, 
    'bitmart': {'USDT': {'available': 3245.671114700832, 'total': 3245.671114700832}, 'ETH': {'available': 1, 'total': 1}, 'SOL': {'available': 2.0, 'total': 2.0}, 'ADA': {'available': -49.15000000000009, 'total': -49.15000000000009}, 'BNB': {'available': 2.0, 'total': 2.0}, 'DOGE': {'available': 30000, 'total': 30000}}, 
    'coinstore': {'USDT': {'available': 76.34606857236179, 'total': 76.34606857236179}, 'ETH': {'available': 0, 'total': 0}, 'SOL': {'available': 0.0, 'total': 0.0}, 'ADA': {'available': 0.0, 'total': 0.0}, 'BNB': {'available': 0.0, 'total': 0.0}, 'DOGE': {'available': 0, 'total': 0}}, 
    'ascendex': {'USDT': {'available': -0.04927123712923276, 'total': -0.04927123712923276}, 'ETH': {'available': 1, 'total': 1}, 'SOL': {'available': 2.0, 'total': 2.0}, 'ADA': {'available': 85.0, 'total': 85.0}, 'BNB': {'available': 2.0, 'total': 2.0}, 'DOGE': {'available': 6000.0, 'total': 6000.0}}, 
    'binance': {'USDT': {'available': 15036.833423349999, 'total': 15036.833423349999}, 'ETH': {'available': 1, 'total': 1}, 'SOL': {'available': 2.0, 'total': 2.0}, 'ADA': {'available': 4715.0, 'total': 4715.0}, 'BNB': {'available': 13.992, 'total': 13.992}, 'DOGE': {'available': 1377.0, 'total': 1377.0}}
}
        
print('total_balance_initial', calculate_total_balance(BALANCES_INITIAL))
        
print('total_balance_final', calculate_total_balance(BALANCES_FINAL))

bot_db = get_bot_db(db_connection='bot', bot_type='arbitrage')

EXCHANGES = ['tidex', 'mexc', 'bitmart', 'coinstore', 'ascendex', 'binance']
BASE_ASSETS = ['ADA', 'DOGE', 'SOL', 'BNB']
#EXCHANGES = ['tidex', 'mexc', 'bitmart', 'coinstore', 'ascendex']

trades_total: list[Trade] = []

for exchange in EXCHANGES:
    for base_asset in BASE_ASSETS:
        trades = asyncio.run(bot_db.fetch_trades_db(exchange=exchange, base_asset=base_asset, quote_asset='USDT', initial_timestamp=1720292802158, trade_side=TradeSide.SELL))
        trades_total.extend(trades)
        trades = asyncio.run(bot_db.fetch_trades_db(exchange=exchange, base_asset=base_asset, quote_asset='USDT', initial_timestamp=1720292802158, trade_side=TradeSide.BUY))
        trades_total.extend(trades)

trades_total.sort(key=lambda trade: int(trade.timestamp), reverse=False)

#print('trades_total', trades_total, len(trades_total))

#raise

BALANCES_CALCULATED = BALANCES_INITIAL.copy()

i = 0
for trade in trades_total:
    i += 1
    cost_base = 0
    if trade.fee['currency'] == trade.base_asset:
        cost_base = trade.fee['cost']
    cost_quote = 0
    if trade.fee['currency'] == trade.quote_asset:
        cost_quote = trade.fee['cost']
    if trade.side == TradeSide.BUY:
        BALANCES_CALCULATED[trade.exchange][trade.base_asset]['available'] += (trade.amount - cost_base)
        BALANCES_CALCULATED[trade.exchange][trade.base_asset]['total'] += (trade.amount - cost_base)
        BALANCES_CALCULATED[trade.exchange][trade.quote_asset]['available'] -= (trade.amount * trade.price + cost_quote)
        BALANCES_CALCULATED[trade.exchange][trade.quote_asset]['total'] -= (trade.amount * trade.price + cost_quote)
        858.43196715 -42.15004714999964
        if BALANCES_CALCULATED[trade.exchange][trade.quote_asset]['available'] < 0:
            print('----------------PROBLEM 1', BALANCES_CALCULATED[trade.exchange][trade.quote_asset]['available'] + trade.amount * trade.price, trade.amount * trade.price / 0.98)
            #break
    else:
        BALANCES_CALCULATED[trade.exchange][trade.base_asset]['available'] -= (trade.amount + cost_base)
        BALANCES_CALCULATED[trade.exchange][trade.base_asset]['total'] -= (trade.amount + cost_base)
        BALANCES_CALCULATED[trade.exchange][trade.quote_asset]['available'] += (trade.amount * trade.price - cost_quote)
        BALANCES_CALCULATED[trade.exchange][trade.quote_asset]['total'] += (trade.amount * trade.price - cost_quote)
        if BALANCES_CALCULATED[trade.exchange][trade.base_asset]['available'] < 0:
            print('----------------PROBLEM 2', BALANCES_CALCULATED[trade.exchange][trade.base_asset]['available'] + trade.amount, trade.amount / 0.98)
            #break
    print('trade', i, trade.exchange, trade.base_asset, trade.quote_asset, trade.side.name, trade.price, trade.amount, trade.fee)
    if i >= 100:
        break

print('BALANCES_CALCULATED', BALANCES_CALCULATED)

print('total_balance_calculated', calculate_total_balance(BALANCES_CALCULATED))