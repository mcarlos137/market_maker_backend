import os
import sys
sys.path.append(os.getcwd())
from vol.base import VolBotBase, VolBot
from damexCommons.businesses.ascendex import AscendexSimpleBusiness
from damexCommons.businesses.coinstore import CoinstoreSimpleBusiness
from damexCommons.businesses.tidex import TidexSimpleBusiness
    

class VolBotDefault(VolBot):
    
    def __init__(self, vol_bot_base: VolBotBase) -> None:
        super().__init__(vol_bot_base=vol_bot_base)
        

class VolBotDefaultAscendex(VolBotDefault, AscendexSimpleBusiness):
    
    def __init__(self, vol_bot_base: VolBotBase) -> None:
        super().__init__(vol_bot_base=vol_bot_base)
        
        
class VolBotDefaultCoinstore(VolBotDefault, CoinstoreSimpleBusiness):
    
    def __init__(self, vol_bot_base: VolBotBase) -> None:
        super().__init__(vol_bot_base=vol_bot_base)
        
        
class VolBotDefaultTidex(VolBotDefault, TidexSimpleBusiness):
    
    def __init__(self, vol_bot_base: VolBotBase) -> None:
        super().__init__(vol_bot_base=vol_bot_base)