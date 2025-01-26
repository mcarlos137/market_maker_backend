import time
from threading import Event
import logging
import random

import os
import sys
sys.path.append(os.getcwd())
from maker.base import MakerBotBase, MakerBot
#from damexCommons.base import OrderStatus, Trade, TradeSide, Order, OrderSide


class MakerBotCLOB(MakerBot):
    
    def __init__(self, maker_bot_base: MakerBotBase) -> None:
        super().__init__(maker_bot_base=maker_bot_base)
                        