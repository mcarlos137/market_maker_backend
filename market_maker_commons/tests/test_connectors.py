import ccxt
import os
import json
import asyncio
from pathlib import Path
from damexCommons.connectors.bitmart import BitmartCommons

#with open(str(Path(os.getcwd()).parent) + "/base/apis.json", encoding='UTF-8') as f:
#    apis = json.load(f)     
#    api_key = apis['bitmart__main']['api_key']
#    api_secret = apis['bitmart__main']['api_secret']
#    api_memo = apis['bitmart__main']['api_memo']
        
#commons = BitmartCommons(exchange_connector=ccxt.bitmart({'apiKey': api_key, 'secret': api_secret, 'uid': api_memo}), base_asset='NONE', quote_asset='NONE')

#def test_fetch_balance():
#    bitmart_commons = BitmartCommons(exchange_connector=ccxt.bitmart({'apiKey': api_key, 'secret': api_secret, 'uid': api_memo}), base_asset='NONE', quote_asset='NONE')
#    balance = asyncio.run(bitmart_commons.fetch_balance())
#    assert len(balance) > 0 
