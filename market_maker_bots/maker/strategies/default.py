import os
import sys
sys.path.append(os.getcwd())
from maker.base import MakerBotBase, MakerBot
from damexCommons.businesses.ascendex import AscendexSimpleBusiness
from damexCommons.businesses.coinstore import CoinstoreSimpleBusiness
from damexCommons.businesses.tidex import TidexSimpleBusiness


class MakerBotDefault(MakerBot):
    
    def __init__(self, maker_bot_base: MakerBotBase) -> None:
        super().__init__(maker_bot_base=maker_bot_base)
        
        
class MakerBotDefaultAscendex(MakerBotDefault, AscendexSimpleBusiness):
    
    def __init__(self, maker_bot_base: MakerBotBase) -> None:
        super().__init__(maker_bot_base=maker_bot_base)
        
        
class MakerBotDefaultCoinstore(MakerBotDefault, CoinstoreSimpleBusiness):
    
    def __init__(self, maker_bot_base: MakerBotBase) -> None:
        super().__init__(maker_bot_base=maker_bot_base)
        

class MakerBotDefaultTidex(MakerBotDefault, TidexSimpleBusiness):
    
    def __init__(self, maker_bot_base: MakerBotBase) -> None:
        super().__init__(maker_bot_base=maker_bot_base)