import json
from solana.rpc.api import Client
from solana.rpc.types import TokenAccountOpts
from solders.rpc.responses import GetBalanceResp, GetTokenAccountsByOwnerJsonParsedResp
from solders.pubkey import Pubkey
from damexCommons.base import TradeSide
from damexCommons.connectors.base import LPCommons
from damexCommons.tools.utils import http_request_damex, SOLANA_TOKENS


PROGRAM_ID: str = 'TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA'

class RaydiumCommons(LPCommons):
    
    def __init__(self, chain: str, network: str, connector: str, address: str, base_asset: str, quote_asset: str) -> None:
        LPCommons.__init__(
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
    
    async def simulate_swap_transaction(self, trade_side: TradeSide, amount: float) -> dict:
        simulation = await http_request_damex(
            method='POST',
            url='http://localhost:3000/swap/sendTransaction',
            data={
                'pair': self.exchange_pair,
                'tradeSide': trade_side.name,
                'amount': amount,
                'executionType': 'SIMULATE'
            },
            retry=1
        )
        return simulation

    async def send_swap_transaction(self, trade_side: TradeSide, amount: float, price: float) -> dict:
        tx = await http_request_damex(
            method='POST',
            url='http://localhost:3000/swap/sendTransaction',
            data={
                'pair': self.exchange_pair,
                'tradeSide': trade_side.name,
                'amount': amount,
                'executionType': 'SEND'
            },
            retry=1
        )
        return tx
            
    async def fetch_swap_prices(self, trade_side: TradeSide, amount: float) -> dict:
        swap_prices = await http_request_damex(
            method='GET',
            url='http://localhost:3000/swap/fetchPrices?pair=%s&tradeSide=%s&amount=%s' % (self.exchange_pair, trade_side.name, amount),
            retry=1
        )
        return swap_prices
                        
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
    
    async def fetch_ticker(self) -> dict:
        raise NotImplementedError
    
    async def fetch_tickers(self, markets: list[str]) -> list[dict]:
        raise NotImplementedError