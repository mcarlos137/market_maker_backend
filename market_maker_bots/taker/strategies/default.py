import os
import sys
sys.path.append(os.getcwd())
from taker.base import TakerBotBase, TakerBot
from damexCommons.businesses.ascendex import AscendexSimpleBusiness
from damexCommons.businesses.coinstore import CoinstoreSimpleBusiness
from damexCommons.businesses.tidex import TidexSimpleBusiness


class TakerBotDefault(TakerBot):
    
    def __init__(self, taker_bot_base: TakerBotBase) -> None:
        super().__init__(taker_bot_base=taker_bot_base)
        
        
class TakerBotDefaultAscendex(TakerBotDefault, AscendexSimpleBusiness):
    
    def __init__(self, taker_bot_base: TakerBotBase) -> None:
        super().__init__(taker_bot_base=taker_bot_base)
        
        
class TakerBotDefaultCoinstore(TakerBotDefault, CoinstoreSimpleBusiness):
    
    def __init__(self, taker_bot_base: TakerBotBase) -> None:
        super().__init__(taker_bot_base=taker_bot_base)
        

class TakerBotDefaultTidex(TakerBotDefault, TidexSimpleBusiness):
    
    def __init__(self, taker_bot_base: TakerBotBase) -> None:
        super().__init__(taker_bot_base=taker_bot_base)