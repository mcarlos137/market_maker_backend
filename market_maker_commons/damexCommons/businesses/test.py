from threading import Event
from damexCommons.businesses.base import SimpleBusiness
from damexCommons.connectors.base import ExchangeCommons
from damexCommons.tools.bot_db import BotDB

class TestBusiness(SimpleBusiness):
    
    __test__ = False
    
    def __init__(self, 
                 bot_id: str,
                 bot_type: str,
                 active: bool,
                 bot_db: BotDB, 
                 commons: dict[str, ExchangeCommons],
                 exchange: str, 
                 base_asset: str,
                 quote_asset: str,
                 tick_time: int,
                 ) -> None:
        
        SimpleBusiness.__init__(
            self,
            bot_id=bot_id,
            bot_type=bot_type,
            active=active,
            bot_db=bot_db,
            commons=commons,
            exchange=exchange,
            base_asset=base_asset,
            quote_asset=quote_asset,
            tick_time=tick_time
        )  
            
    async def start(self) -> None:
        pass
    
    def strategy_check_thread(self, event: Event) -> None:
        pass
