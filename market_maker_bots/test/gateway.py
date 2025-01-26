import asyncio
from enum import Enum
from pathlib import Path
import json
import os
import sys
sys.path.append(os.getcwd())

from damexCommons.tools.gateway_http_client import GatewayHttpClient, TradeType
from damexCommons.tools.ethereum_graphql_client import EthereumGraphQLClient

# 0x68a039EF94D010565e8Ba84F2bA4D50b8d1fc7F7

# 0x68a039ef94d010565e8ba84f2ba4d50b8d1fc7f7
# 0xd5dbbd1f7bb95197523844c5a53685e30c29b457224133d6f189e9432683046d
        
gateway_http_client = GatewayHttpClient(base_url='https://localhost:15888')
ethereum_graphql_client = EthereumGraphQLClient()

# OK
#response = asyncio.run(gateway_http_client.ping_gateway())
#print('response1', response)

# OK
response = asyncio.run(gateway_http_client.get_connectors())
print('response2', response)

# OK
#response = asyncio.run(gateway_http_client.get_wallets())
#print('response3', response)

# OK
#response = asyncio.run(gateway_http_client.get_configuration())
#print('response4', response)

# OK
#response = asyncio.run(gateway_http_client.get_tokens(chain='ethereum', network='mainnet'))
#print('response5', response)

# OK
#response = asyncio.run(gateway_http_client.get_network_status(chain='ethereum', network='mainnet'))
#print('response6', response)

# OK
#response = asyncio.run(gateway_http_client.get_balances(chain='ethereum', network='mainnet', address='0x68a039EF94D010565e8Ba84F2bA4D50b8d1fc7F7', token_symbols=['ETH', 'USDT', 'DAMEX']))
#print('response7', response)

# FAILED
#response = asyncio.run(gateway_http_client.get_price(chain='ethereum', network='mainnet', connector='uniswap', base_asset='DAMEX', quote_asset='USDT', amount=10.0, side=TradeType.SELL))
#print('response8', response)

# OK
#response = asyncio.run(gateway_http_client.add_wallet(chain='ethereum', network='mainnet', private_key='0xd5dbbd1f7bb95197523844c5a53685e30c29b457224133d6f189e9432683046d'))
#print('response9', response)

# OK
#response = asyncio.run(gateway_http_client.get_transaction_status(chain='ethereum', network='mainnet', transaction_hash='0xa370ce8941947a7783bc18cfe50928e620ae2a56f715e71ca1e11675fc8bd159'))
#print('response12', response)

# 0xa370ce8941947a7783bc18cfe50928e620ae2a56f715e71ca1e11675fc8bd159 OK
# 0x548cf4da9317f6389a90ebbdc1ba9d3b3034a904936ae3c36a216827cc20e134 PENDING


# OK
#response = asyncio.run(gateway_http_client.get_allowances(chain='ethereum', network='mainnet', address='0x68a039EF94D010565e8Ba84F2bA4D50b8d1fc7F7', token_symbols=['USDT', 'ETH', 'DAMEX'], spender='0x68a039EF94D010565e8Ba84F2bA4D50b8d1fc7F7'))
#print('response14', response)

# OK
#response = asyncio.run(gateway_http_client.get_nonce(chain='ethereum', network='mainnet', address='0x68a039EF94D010565e8Ba84F2bA4D50b8d1fc7F7'))
#print('response15', response)

# FAILED
#response = asyncio.run(gateway_http_client.approve_token(chain='ethereum', network='mainnet', address='0x68a039EF94D010565e8Ba84F2bA4D50b8d1fc7F7', token='USDT', spender='0x68a039EF94D010565e8Ba84F2bA4D50b8d1fc7F7'))
#print('response13', response)


########## AMM

# OK
#response = asyncio.run(gateway_http_client.amm_estimate_gas(chain='ethereum', network='mainnet', connector='uniswap'))
#print('response10', response)

# FAILED (GAS)
'''
response = asyncio.run(
    gateway_http_client.amm_lp_add(
        chain='ethereum', 
        network='mainnet', 
        connector='uniswapLP',
        #connector='pancakeswapLP',
        address='0x68a039EF94D010565e8Ba84F2bA4D50b8d1fc7F7',
        token0='DAMEX',
        token1='USDT',
        amount0=Decimal(500),
        amount1=Decimal(22),
        fee='HIGH',
        lowerPrice=Decimal(0.043),
        upperPrice=Decimal(0.045),
        #max_fee_per_gas=30
        )
    )
print('response16', response)
'''

# nonce: Optional[int] = None,

# PENDING (amm_lp_add first)
'''
response = asyncio.run(
    gateway_http_client.amm_lp_remove(
        chain='ethereum', 
        network='mainnet', 
        connector='uniswapLP',
        address='0x68a039EF94D010565e8Ba84F2bA4D50b8d1fc7F7',
        token_id=696986,
        decreasePercent=20
        )
    )
print('response17', response)
'''

# nonce: Optional[int] = None,

# OK
'''
amount0 = 0
amount1 = 0
unclaimedToken0 = 0
unclaimedToken1 = 0
amm_lp = asyncio.run(ethereum_graphql_client.get_amm_lp(id='0xb47bd400eea9497531073a24afc29c1a96185253'))
amm_lp_positions = asyncio.run(ethereum_graphql_client.get_amm_lp_positions(pool_id='0xb47bd400eea9497531073a24afc29c1a96185253'))
amm_lp['chain'] = 'ethereum'
amm_lp['network'] = 'mainnet'
amm_lp['connector'] = 'uniswapLP'
amm_lp['token0'] = 'DAMEX'
amm_lp['token1'] = 'USDT'
amm_lp['positions'] = []
amm_lp['amount0'] = 0
amm_lp['amount1'] = 0
amm_lp['unclaimedToken0'] = 0
amm_lp['unclaimedToken1'] = 0
for amm_lp_position in amm_lp_positions:
    token_id = int(amm_lp_position['id'])
    amm_lp_position_gateway = asyncio.run(
            gateway_http_client.amm_lp_position(
                chain='ethereum', 
                network='mainnet', 
                connector='uniswapLP',
                token_id=token_id
            )
    )
    del amm_lp_position_gateway['network']
    del amm_lp_position_gateway['latency']
    amm_lp_position_gateway['id'] = token_id
    amm_lp_position_gateway['owner'] = amm_lp_position['owner']
    amm_lp['positions'].append(amm_lp_position_gateway)
    amm_lp['amount0'] += float(amm_lp_position_gateway['amount0'])
    amm_lp['amount1'] += float(amm_lp_position_gateway['amount1'])
    amm_lp['unclaimedToken0'] += float(amm_lp_position_gateway['unclaimedToken0'])
    amm_lp['unclaimedToken1'] += float(amm_lp_position_gateway['unclaimedToken1'])

print('amm_lp', amm_lp)
'''
'''
token_ids = [496566, 496629, 496632, 496636, 496637, 496639, 496693, 541738, 541740, 545284, 545286, 545288, 545417, 545418, 696986]
for token_id in token_ids:
    response = asyncio.run(
            gateway_http_client.amm_lp_position(
                chain='ethereum', 
                network='mainnet', 
                connector='uniswapLP',
                token_id=token_id
                )
        )
    amount0 += float(response['amount0'])
    amount1 += float(response['amount1'])
    unclaimedToken0 += float(response['unclaimedToken0'])
    unclaimedToken1 += float(response['unclaimedToken1'])
    print('response11', token_id, response)

print('amount0---------------------->', amount0)
print('amount1---------------------->', amount1)
print('unclaimedToken0---------------------->', unclaimedToken0)
print('unclaimedToken1---------------------->', unclaimedToken1)
'''

########### CLOB

'''
response = asyncio.run(
    gateway_http_client.get_clob_orderbook_snapshot(
        chain='avalanche', 
        network='dexalot', 
        connector='dexalot',
        trading_pair='BTC.B-USDC'
        )
    )
print('response18', response)
'''

'''
response = asyncio.run(
    gateway_http_client.get_clob_ticker(
        chain='ethereum', 
        network='mainnet', 
        connector='uniswap',
        trading_pair='ETH-USDT'
        )
    )
print('response19', response)
'''

'''
response = asyncio.run(
    gateway_http_client.clob_place_order(
        chain='ethereum', 
        network='mainnet', 
        connector='uniswap',
        trading_pair='DAMEX-USDT',
        address='0x68a039EF94D010565e8Ba84F2bA4D50b8d1fc7F7',
        trade_type=TradeType.BUY,
        order_type=OrderType.LIMIT,
        price=Decimal(0.042),
        size=Decimal(50),
        client_order_id='AAAAAAABBBBBBB'
        )
    )
print('response20', response)
'''
