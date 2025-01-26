import logging
from decimal import Decimal
from damexCommons.base import TradeSide
from damexCommons.connectors.base import LPCommons
from damexCommons.tools.gateway_http_client import GatewayHttpClient


class GatewayCommons(LPCommons):
    
    def __init__(self, chain: str, network: str, connector: str, address: str, base_asset: str, quote_asset: str):
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
        self.gatewayHttpClient = GatewayHttpClient(base_url='https://localhost:15888')
        
    @property
    def exchange_pair(self) -> str:
        return self.base_asset + '-' + self.quote_asset

    async def simulate_swap_transaction(self, trade_side: TradeSide, amount: float) -> dict:
        raise NotImplementedError
    
    async def send_swap_transaction(self, trade_side: TradeSide, amount: float, price: float) -> dict:
        try:
            rsp = self.gatewayHttpClient.amm_trade(
                chain=self.chain, 
                network=self.network, 
                connector=self.exchange,
                address=self.address,
                base_asset=self.base_asset,
                quote_asset=self.quote_asset,
                side=trade_side,
                amount=Decimal(amount), 
                price=Decimal(price)
            )
            logging.info('send trade %s', rsp)
            return rsp['txHash']
        except Exception as e:
            raise e
    
    async def fetch_swap_prices(self, trade_side: TradeSide, amount: float) -> dict:
        try:
            rsp = self.gatewayHttpClient.get_price(
                chain=self.chain, 
                network=self.network, 
                connector=self.exchange,
                base_asset=self.base_asset,
                quote_asset=self.quote_asset,
                amount=Decimal(amount), 
                side=trade_side
            )    
            logging.info('price params %s', rsp)
            return rsp
        except Exception as e:
            raise e
    
    async def fetch_balance(self) -> dict:
        try:
            rsp = self.gatewayHttpClient.get_balances(
                chain=self.chain, 
                network=self.network, 
                address=self.address, 
                token_symbols=['ETH', 'USDT', 'DAMEX']
            )                 
            data = rsp['balances']
            balance = {}
            currencys = []
            for coin in data:
                currencys.append(coin)
            currencys = list(set(currencys))
            for currency in currencys:
                balance[currency] = {}
                for coin in data:
                    if coin == currency:
                        balance[currency]['available'] = data[coin]
                        balance[currency]['frozen'] = 0

                balance[currency]['total'] = str(float(balance[currency]['available']) + float(balance[currency]['frozen']))
            logging.info('balance %s', balance)
            return balance
        except Exception as e:
            raise e
        
    async def fetch_ticker(self) -> dict:
        raise NotImplementedError
    
    async def fetch_tickers(self, markets: list[str]) -> list[dict]:
        raise NotImplementedError
