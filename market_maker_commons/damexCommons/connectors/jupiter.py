import json
import requests
import logging
from solana.rpc.api import Client
from solana.rpc.types import TokenAccountOpts
from solders.rpc.responses import GetBalanceResp, GetTokenAccountsByOwnerJsonParsedResp
from solders.pubkey import Pubkey
from damexCommons.base import OrderSide, Order, Trade
from damexCommons.connectors.base import CLOBCommons
from damexCommons.tools.utils import http_request_damex, SOLANA_TOKENS


PROGRAM_ID: str = 'TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA'

class JupiterCommons(CLOBCommons):
    
    def __init__(self, chain: str, network: str, connector: str, address: str, base_asset: str, quote_asset: str) -> None:
        CLOBCommons.__init__(
            self,
            exchange_connector=None,
            exchange=connector,
            base_asset=base_asset,
            quote_asset=quote_asset
        )
        self.chain = chain
        self.network = network
        self.address = address
        self.rpc_url = 'https://api.mainnet-beta.solana.com'
        self.api_client = Client(self.rpc_url)
        
    @property
    def exchange_pair(self) -> str:
        return self.base_asset + '-' + self.quote_asset
                        
    async def create_limit_order(self, order_side: OrderSide, price: float, amount: float) -> str:
        order_id = await http_request_damex(
            method='POST',
            url='http://localhost:3001/trade/createLimitOrder',
            data={
                'pair': self.exchange_pair,
                'orderSide': order_side,
                'amount': amount,
                'price': price
            },
            retry=1
        )
        return order_id
    
    async def cancel_limit_order(self, order_id: str) -> None:
        await http_request_damex(
            method='POST',
            url='http://localhost:3001/trade/cancelOrder',
            data={
                'orderPublicKey': order_id,
            },
            retry=1
        )
        
    async def fetch_market_price(self) -> float:
        try:
            market_price_response = requests.get('https://price.jup.ag/v6/price?ids=%s&vsToken=%s' % (self.base_asset, self.quote_asset), timeout=7)
            market_price_response.raise_for_status()
            return market_price_response.json()['data'][self.base_asset]['price']
        except requests.exceptions.HTTPError as e:
            logging.getLogger(__name__).error(e.response.text)   
    
        
    async def fetch_orders_history(self) -> list[Order]:
        orders_history = await http_request_damex(
            method='GET',
            url='http://localhost:3001/trade/getOrderHistory',
            retry=1
        )
        return orders_history
    
    async def fetch_trades_history(self) -> list[Trade]:
        trades_history = await http_request_damex(
            method='GET',
            url='http://localhost:3001/trade/getTradeHistory',
            retry=1
        )
        return trades_history
            
    async def fetch_balance(self) -> dict:
        pub_key = Pubkey.from_string(self.address)
        pub_key_token = Pubkey.from_string(PROGRAM_ID)
        get_balance_response: GetBalanceResp = self.api_client.get_balance(pub_key)
        get_balance = json.loads(get_balance_response.to_json())
        get_token_accounts_by_owner_json_parsed_response: GetTokenAccountsByOwnerJsonParsedResp = self.api_client.get_token_accounts_by_owner_json_parsed(owner=pub_key, opts=TokenAccountOpts(program_id=pub_key_token))
        get_token_accounts_by_owner_json_parsed = json.loads(get_token_accounts_by_owner_json_parsed_response.to_json())
        balance = {
            'SOL': {
                'available': float(get_balance['result']['value']) / 1e9,
                'total': float(get_balance['result']['value']) / 1e9
            }
        }
        for value in get_token_accounts_by_owner_json_parsed['result']['value']:
            token = value['account']['data']['parsed']['info']
            if token['mint'] not in SOLANA_TOKENS:
                continue
            balance[SOLANA_TOKENS[token['mint']]] = {
                'available': float(token['tokenAmount']['uiAmount']),
                'total': float(token['tokenAmount']['uiAmount'])
            }
        return balance