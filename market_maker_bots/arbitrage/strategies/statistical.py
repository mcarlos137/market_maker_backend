import os
import sys
sys.path.append(os.getcwd())
from arbitrage.base import ArbitrageBotBase, ArgitrageBot

class ArbitrageBotStatistical(ArgitrageBot):
    
    def __init__(self, arbitrage_bot_base: ArbitrageBotBase) -> None:
        super().__init__(arbitrage_bot_base=arbitrage_bot_base)
            