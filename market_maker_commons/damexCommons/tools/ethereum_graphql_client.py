import logging
from typing import Any, Dict, Optional
import requests

class EthereumGraphQLClient:
    
    _logger: Optional[logging.Logger] = None
        
    def __init__(self):
        self.base_url = 'https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3'
        
    @classmethod
    def logger(cls) -> logging.Logger:
        if cls._logger is None:
            cls._logger = logging.getLogger(__name__)
        return cls._logger
    
    async def get_amm_lp(self, pool_id: str) -> Dict[str, Any]:
        query = """
            {
                pool(id: "%s"){
                    id
                    volumeToken0
                    volumeToken1
                    txCount
                    swaps(orderBy: timestamp, orderDirection: desc) {
                        id
                        timestamp
                        sender
                        recipient
                        amount0
                        amount1
                        origin
                    }
                }  
            }
            """ % (pool_id)
        try:
            response: Dict[str, Any] = requests.post(url=self.base_url, json={"query": query}, timeout=7)
            return response.json()['data']['pool']
        except Exception:
            self.logger().error(
                "Error fetching gateway status info",
                exc_info=True
            )
        
    async def get_amm_lp_positions(self, pool_id: str) -> Dict[str, Any]:
        query = """
            {
                positions(where: {pool: "%s"}){
                    id 
                    owner
                    depositedToken0
                    depositedToken1
                    withdrawnToken0
                    withdrawnToken1   
                }  
            }
            """ % (pool_id)
        try:
            response: Dict[str, Any] = requests.post(url=self.base_url, json={"query": query}, timeout=7)
            return response.json()['data']['positions']
        except Exception:
            self.logger().error(
                "Error fetching gateway status info",
                exc_info=True
            )