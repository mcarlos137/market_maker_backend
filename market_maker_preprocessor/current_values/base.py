import sys
import os
sys.path.append(os.getcwd())
from period_data_type import PeriodDataType
from tools.utils import get_new_file_data_for_pnl_values_ticker

             
class CurrentValuesPeriodDataType(PeriodDataType):
        
    def __init__(self, exchange: str, base_asset: str, quote_asset: str) -> None:
        PeriodDataType.__init__(
            self, 
            exchange=exchange, 
            base_asset=base_asset, 
            quote_asset=quote_asset, 
            operation='current_values',
            file_data_callback=get_new_file_data_for_pnl_values_ticker
        )