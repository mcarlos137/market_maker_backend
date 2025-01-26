import logging
import re
import ssl
import aiohttp
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Union

class TradeType(Enum):
    BUY = 1
    SELL = 2
    RANGE = 3
        
class OrderType(Enum):
    MARKET = 1
    LIMIT = 2
    LIMIT_MAKER = 3

    def is_limit_type(self):
        return self in (OrderType.LIMIT, OrderType.LIMIT_MAKER)
    
class GatewayHttpClient:
    
    _logger: Optional[logging.Logger] = None
    _shared_client: Optional[aiohttp.ClientSession] = None
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        
    @classmethod
    def logger(cls) -> logging.Logger:
        if cls._logger is None:
            cls._logger = logging.getLogger(__name__)
        return cls._logger
    
    @staticmethod
    def is_timeout_error(e) -> bool:
        """
        It is hard to consistently return a timeout error from gateway
        because it uses many different libraries to communicate with the
        chains with their own idiosyncracies and they do not necessarilly
        return HTTP status code 504 when there is a timeout error. It is
        easier to rely on the presence of the word 'timeout' in the error.
        """
        error_string = str(e)
        if re.search('timeout', error_string, re.IGNORECASE):
            return True
        return False
    
    @classmethod
    def _http_client(cls, re_init: bool = False) -> aiohttp.ClientSession:
        """
        :returns Shared client session instance
        """
        if cls._shared_client is None or re_init:
            cert_path = '/mnt/data/market_maker_gateway_certs'
            ssl_ctx = ssl.create_default_context(cafile=f"{cert_path}/ca_cert.pem")
            ssl_ctx.load_cert_chain(certfile=f"{cert_path}/client_cert.pem",
                                    keyfile=f"{cert_path}/client_key.pem",
                                    password='mm'
                                    )
            conn = aiohttp.TCPConnector(ssl=ssl_ctx)
            cls._shared_client = aiohttp.ClientSession(connector=conn)
        return cls._shared_client
    
    async def api_request(
            self,
            method: str,
            path_url: str,
            params: Dict[str, Any] = {},
            fail_silently: bool = False,
            use_body: bool = False,
    ) -> Optional[Union[Dict[str, Any], List[Dict[str, Any]]]]:
        """
        Sends an aiohttp request and waits for a response.
        :param method: The HTTP method, e.g. get or post
        :param path_url: The path url or the API end point
        :param params: A dictionary of required params for the end point
        :param fail_silently: used to determine if errors will be raise or silently ignored
        :param use_body: used to determine if the request should sent the parameters in the body or as query string
        :returns A response in json format.
        """
        url = f"{self.base_url}/{path_url}"
        client = self._http_client()
        parsed_response = {}
        
        try:
            if method == "get":
                if len(params) > 0:
                    if use_body:
                        response = await client.get(url, json=params)
                    else:
                        response = await client.get(url, params=params)
                else:
                    response = await client.get(url)
            elif method == "post":
                response = await client.post(url, json=params)
            elif method == 'put':
                response = await client.put(url, json=params)
            elif method == 'delete':
                response = await client.delete(url, json=params)
            else:
                raise ValueError(f"Unsupported request method {method}")
            if not fail_silently and response.status == 504:
                self.logger().error(f"The network call to {url} has timed out.")
            else:
                logging.info('response----------------------------- %s', response)
                self.logger().info(f"Response {response}")
                parsed_response = await response.json()
                if response.status != 200 and not fail_silently and not self.is_timeout_error(parsed_response):
                    logging.error('----------------------------- %s', parsed_response)

                    if "error" in parsed_response:
                        raise ValueError(f"Error on {method.upper()} {url} Error: {parsed_response['error']}")
                    else:
                        raise ValueError(f"Error on {method.upper()} {url} Error: {parsed_response}")
                    
        except Exception as e:
            if not fail_silently:
                if self.is_timeout_error(e):
                    self.logger().error(f"The network call to {url} has timed out.")
                else:
                    self.logger().error(
                        e,
                        exc_info=True
                    )
            raise e

        return parsed_response

    # OK - BASE
    async def ping_gateway(self) -> bool:
        try:
            response: Dict[str, Any] = await self.api_request("get", "", fail_silently=True)
            return response["status"] == "ok"
        except Exception:
            return False

    # OK - BASE
    async def get_gateway_status(self, fail_silently: bool = False) -> List[Dict[str, Any]]:
        """
        Calls the status endpoint on Gateway to know basic info about connected networks.
        """
        try:
            return await self.get_network_status(fail_silently=fail_silently)
        except Exception as e:
            self.logger().error(
                "Error fetching gateway status info %s", e,
                exc_info=True
            )

    # OK - BASE
    async def get_connectors(self, fail_silently: bool = False) -> Dict[str, Any]:
        return await self.api_request("get", "connectors", fail_silently=fail_silently)

    # OK - BASE
    async def get_wallets(self, fail_silently: bool = False) -> List[Dict[str, Any]]:
        return await self.api_request("get", "wallet", fail_silently=fail_silently)
    
    # OK - BASE
    async def add_wallet(
        self, chain: str, network: str, private_key: str, **kwargs
    ) -> Dict[str, Any]:
        request = {"chain": chain, "network": network, "privateKey": private_key}
        request.update(kwargs)
        return await self.api_request(method="post", path_url="wallet/add", params=request)

    # OK - BASE - ?
    async def get_configuration(self, fail_silently: bool = False) -> Dict[str, Any]:
        return await self.api_request("get", "chain/config", fail_silently=fail_silently)

    # OK - BASE
    async def get_balances(
            self,
            chain: str,
            network: str,
            address: str,
            token_symbols: List[str],
            connector: str = None,
            fail_silently: bool = False,
    ) -> Dict[str, Any]:
        if isinstance(token_symbols, list):
            token_symbols = [x for x in token_symbols if isinstance(x, str) and x.strip() != '']
            network_path = "near" if chain == "near" else "chain"
            request_params = {
                "chain": chain,
                "network": network,
                "address": address,
                "tokenSymbols": token_symbols,
            }
            if connector is not None:
                request_params["connector"] = connector
            return await self.api_request(
                method="post",
                path_url=f"{network_path}/balances",
                params=request_params,
                fail_silently=fail_silently,
            )
        else:
            return {}

    # OK - BASE
    async def get_tokens(
            self,
            chain: str,
            network: str,
            fail_silently: bool = True
    ) -> Dict[str, Any]:
        network_path = "near" if chain == "near" else "chain"
        return await self.api_request("get", f"{network_path}/tokens", {
            "chain": chain,
            "network": network
        }, fail_silently=fail_silently)

    # OK - BASE
    async def get_network_status(
            self,
            chain: str = None,
            network: str = None,
            fail_silently: bool = False
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        req_data: Dict[str, str] = {}
        if chain is not None and network is not None:
            req_data["chain"] = chain
            req_data["network"] = network
        return await self.api_request("get", "chain/status", req_data, fail_silently=fail_silently)

    # PENDING - BASE
    async def get_price(
            self,
            chain: str,
            network: str,
            connector: str,
            base_asset: str,
            quote_asset: str,
            amount: Decimal,
            side: TradeType,
            fail_silently: bool = False
    ) -> Dict[str, Any]:
        if side not in [TradeType.BUY, TradeType.SELL]:
            raise ValueError("Only BUY and SELL prices are supported.")

        # XXX(martin_kou): The amount is always output with 18 decimal places.
        return await self.api_request("post", "amm/price", {
            "chain": chain,
            "network": network,
            "connector": connector,
            "base": base_asset,
            "quote": quote_asset,
            "amount": f"{amount:.18f}",
            "side": side.name,
            "allowedSlippage": "0/1",  # hummingbot applies slippage itself
        }, fail_silently=fail_silently)

    # OK - MAKER, VOL, TAKER
    async def get_transaction_status(
            self,
            chain: str,
            network: str,
            transaction_hash: str,
            connector: Optional[str] = None,
            address: Optional[str] = None,
            fail_silently: bool = False
    ) -> Dict[str, Any]:
        request = {
            "chain": chain,
            "network": network,
            "txHash": transaction_hash
        }
        if connector:
            request["connector"] = connector
        if address:
            request["address"] = address
        network_path = "near" if chain == "near" else "network"
        return await self.api_request("post", f"{network_path}/poll", request, fail_silently=fail_silently)

    # PENDING - TAKER, VOL
    async def amm_trade(
            self,
            chain: str,
            network: str,
            connector: str,
            address: str,
            base_asset: str,
            quote_asset: str,
            side: TradeType,
            amount: Decimal,
            price: Decimal,
            nonce: Optional[int] = None,
            max_fee_per_gas: Optional[int] = None,
            max_priority_fee_per_gas: Optional[int] = None
    ) -> Dict[str, Any]:
        # XXX(martin_kou): The amount is always output with 18 decimal places.
        request_payload: Dict[str, Any] = {
            "chain": chain,
            "network": network,
            "connector": connector,
            "address": address,
            "base": base_asset,
            "quote": quote_asset,
            "side": side.name,
            "amount": f"{amount:.18f}",
            "limitPrice": str(price),
            "allowedSlippage": "0/1",  # hummingbot applies slippage itself
        }
        if nonce is not None:
            request_payload["nonce"] = int(nonce)
        if max_fee_per_gas is not None:
            request_payload["maxFeePerGas"] = str(max_fee_per_gas)
        if max_priority_fee_per_gas is not None:
            request_payload["maxPriorityFeePerGas"] = str(max_priority_fee_per_gas)
        return await self.api_request("post", "amm/trade", request_payload)

    # OK - TAKER, VOL
    async def amm_estimate_gas(
            self,
            chain: str,
            network: str,
            connector: str,
    ) -> Dict[str, Any]:
        return await self.api_request("post", "amm/estimateGas", {
            "chain": chain,
            "network": network,
            "connector": connector,
        })

    ############## LP endpoints
    # PENDING - MAKER, VOL
    async def amm_lp_add(
            self,
            chain: str,
            network: str,
            connector: str,
            address: str,
            token0: str,
            token1: str,
            amount0: Decimal,
            amount1: Decimal,
            fee: str,
            lowerPrice: Decimal,
            upperPrice: Decimal,
            token_id: Optional[int] = None,
            nonce: Optional[int] = None,
            max_fee_per_gas: Optional[int] = None,
            max_priority_fee_per_gas: Optional[int] = None
    ) -> Dict[str, Any]:
        request_payload: Dict[str, Any] = {
            "chain": chain,
            "network": network,
            "connector": connector,
            "address": address,
            "token0": token0,
            "token1": token1,
            "amount0": f"{amount0:.18f}",
            "amount1": f"{amount1:.18f}",
            "fee": fee,
            "lowerPrice": str(lowerPrice),
            "upperPrice": str(upperPrice),
            "tokenId": token_id,
            "nonce": nonce,
        }
        if token_id is not None:
            request_payload["tokenId"] = int(token_id)
        if nonce is not None:
            request_payload["nonce"] = int(nonce)
        if max_fee_per_gas is not None:
            request_payload["maxFeePerGas"] = str(max_fee_per_gas)
        if max_priority_fee_per_gas is not None:
            request_payload["maxPriorityFeePerGas"] = str(max_priority_fee_per_gas)
        return await self.api_request("post", "amm/liquidity/add", request_payload)

    # PENDING - MAKER, VOL
    async def amm_lp_remove(
            self,
            chain: str,
            network: str,
            connector: str,
            address: str,
            token_id: int,
            decreasePercent: Optional[int] = None,
            nonce: Optional[int] = None,
            max_fee_per_gas: Optional[int] = None,
            max_priority_fee_per_gas: Optional[int] = None
    ) -> Dict[str, Any]:
        request_payload: Dict[str, Any] = {
            "chain": chain,
            "network": network,
            "connector": connector,
            "address": address,
            "tokenId": token_id,
            "decreasePercent": decreasePercent,
            "nonce": nonce,
        }
        if decreasePercent is not None:
            request_payload["decreasePercent"] = int(decreasePercent)
        if nonce is not None:
            request_payload["nonce"] = int(nonce)
        if max_fee_per_gas is not None:
            request_payload["maxFeePerGas"] = str(max_fee_per_gas)
        if max_priority_fee_per_gas is not None:
            request_payload["maxPriorityFeePerGas"] = str(max_priority_fee_per_gas)
        return await self.api_request("post", "amm/liquidity/remove", request_payload)

    # PENDING - MAKER, VOL
    async def amm_lp_collect_fees(
            self,
            chain: str,
            network: str,
            connector: str,
            address: str,
            token_id: int,
            nonce: Optional[int] = None,
            max_fee_per_gas: Optional[int] = None,
            max_priority_fee_per_gas: Optional[int] = None
    ) -> Dict[str, Any]:
        request_payload: Dict[str, Any] = {
            "chain": chain,
            "network": network,
            "connector": connector,
            "address": address,
            "tokenId": token_id,
            "nonce": nonce,
        }
        if nonce is not None:
            request_payload["nonce"] = int(nonce)
        if max_fee_per_gas is not None:
            request_payload["maxFeePerGas"] = str(max_fee_per_gas)
        if max_priority_fee_per_gas is not None:
            request_payload["maxPriorityFeePerGas"] = str(max_priority_fee_per_gas)
        return await self.api_request("post", "amm/liquidity/collect_fees", request_payload)

    # PENDING - MAKER, VOL
    async def amm_lp_position(
            self,
            chain: str,
            network: str,
            connector: str,
            token_id: int,
    ) -> Dict[str, Any]:
        request_payload: Dict[str, Any] = {
            "chain": chain,
            "network": network,
            "connector": connector,
            "tokenId": token_id,
        }
        return await self.api_request("post", "amm/liquidity/position", request_payload)

    # PENDING - MAKER, VOL
    async def amm_lp_price(
            self,
            chain: str,
            network: str,
            connector: str,
            token_0: str,
            token_1: str,
            fee: str,
            period: Optional[int] = 1,
            interval: Optional[int] = 1,
    ) -> Dict[str, Any]:
        request_payload: Dict[str, Any] = {
            "chain": chain,
            "network": network,
            "connector": connector,
            "token0": token_0,
            "token1": token_1,
            "fee": fee,
            "period": period,
            "interval": interval,
        }
        return await self.api_request("post", "amm/liquidity/price", request_payload)
