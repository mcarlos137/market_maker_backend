import ccxt
from pathlib import Path
import json
import os
import sys
sys.path.append(os.getcwd())

if not os.path.exists('trades_mexc.json'):
    with open(str(Path(os.getcwd()).parent) + "/base/apis.json") as f:
        apis = json.load(f)
        api = 'mexc__main'
        exchange_connector=ccxt.mexc3({
                                'apiKey': apis[api]['api_key'],
                                'secret': apis[api]['api_secret']
                            })
        trades = exchange_connector.fetch_my_trades(symbol='DAMEX/USDT', limit=1200, since=1717016400000)
        trades.sort(key=lambda x: x['timestamp'], reverse=True)    
        with open('trades_mexc.json', 'w') as f:
            f.write(json.dumps(trades))
        
trades = json.loads(open('trades_mexc.json', 'r').read())

for trade in trades:
    print('trade', trade)
    id = trade['id']
    query = 'SELECT * FROM trades_damexusdt WHERE exchange = %s AND exchange_id = %s LIMIT 100' % ('\'mexc\'', id)
            
print('len', len(trades))
        
print('first timestamp', trades[0]['timestamp'])
print('last timestamp', trades[len(trades) - 1]['timestamp'])
    
    

