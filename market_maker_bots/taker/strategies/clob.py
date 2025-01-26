import os
import sys
sys.path.append(os.getcwd())
from taker.base import TakerBotBase, TakerBot
#from damexCommons.base import OrderStatus, Trade, TradeSide, Order, OrderSide


class TakerBotCLOB(TakerBot):
    
    def __init__(self, taker_bot_base: TakerBotBase) -> None:
        super().__init__(taker_bot_base=taker_bot_base)
                 