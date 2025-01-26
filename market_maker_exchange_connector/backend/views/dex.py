from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from damexCommons.tools.ethereum_graphql_client import EthereumGraphQLClient
from damexCommons.tools.gateway_http_client import GatewayHttpClient
import asyncio

gateway_http_client = GatewayHttpClient(base_url='https://localhost:15888')
ethereum_graphql_client = EthereumGraphQLClient()

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_liquidity_pools(request):
    
    pool_id = '0xb47bd400eea9497531073a24afc29c1a96185253'
    
    amm_lp = asyncio.run(ethereum_graphql_client.get_amm_lp(pool_id=pool_id))
    amm_lp_positions = asyncio.run(ethereum_graphql_client.get_amm_lp_positions(pool_id=pool_id))
    amm_lp['chain'] = 'ethereum'
    amm_lp['network'] = 'mainnet'
    amm_lp['connector'] = 'uniswap'
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

    return Response(amm_lp)
