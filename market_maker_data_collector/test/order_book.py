import sys
import json
import asyncio
from damexCommons.tools.connections import get_commons

exchange = sys.argv[1]
base_asset = sys.argv[2]
quote_asset = sys.argv[3]

commons = get_commons(
    base_asset=base_asset,
    quote_asset=quote_asset,
    exchange_or_connector=exchange,
    api_or_wallet=exchange + '__' + 'main'
)

async def callback(exchange: str, base_asset: str, quote_asset: str, data: dict) -> None:
    if len(data) == 0:
        return
    sys.exit(-1)
    
thread_id = exchange + '__' + base_asset + '-' + quote_asset
stop_ws = {thread_id: False}

asyncio.run(commons.run_wss(base_asset=base_asset, quote_asset=quote_asset, wss_object='order_book', stop_wss=stop_ws, callback=callback))