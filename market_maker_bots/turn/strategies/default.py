import os
import sys
sys.path.append(os.getcwd())
from turn.base import TurnBotBase, TurnBot
from damexCommons.businesses.ascendex import AscendexSimpleBusiness
from damexCommons.businesses.coinstore import CoinstoreSimpleBusiness
from damexCommons.businesses.tidex import TidexSimpleBusiness


class TurnBotDefault(TurnBot):
    
    def __init__(self, turn_bot_base: TurnBotBase) -> None:
        super().__init__(turn_bot_base=turn_bot_base)
        
        
class TurnBotDefaultAscendex(TurnBotDefault, AscendexSimpleBusiness):
    
    def __init__(self, turn_bot_base: TurnBotBase) -> None:
        super().__init__(turn_bot_base=turn_bot_base)
        
        
class TurnBotDefaultCoinstore(TurnBotDefault, CoinstoreSimpleBusiness):
    
    def __init__(self, turn_bot_base: TurnBotBase) -> None:
        super().__init__(turn_bot_base=turn_bot_base)
        

class TurnBotDefaultTidex(TurnBotDefault, TidexSimpleBusiness):
    
    def __init__(self, turn_bot_base: TurnBotBase) -> None:
        super().__init__(turn_bot_base=turn_bot_base)