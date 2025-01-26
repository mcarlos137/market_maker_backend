import os
import sys
import asyncio
from typing import Dict, Callable, Any, List, NamedTuple, Optional
sys.path.append(os.getcwd())
from damexCommons.tools.connections import get_commons

commons: dict = {}

async def execute(exchange: str, base_asset: str, quote_asset: str, name: str, attributes: tuple) -> Any:
    key: str = exchange + '__' + base_asset + '-' + quote_asset
    api = exchange + '__main'
    print('--------------A', key, api)
    if key not in commons:
        print('--------------B')
        commons[key] = get_commons(base_asset=base_asset, quote_asset=quote_asset, exchange_or_connector=exchange, api_or_wallet=api)
        print('--------------C', commons)
    return await getattr(commons[key], name)(*attributes)


balance = asyncio.run(execute(exchange='tidex', base_asset='DAMEX', quote_asset='USDT', name='fetch_balance', attributes=()))

print('balance', balance)