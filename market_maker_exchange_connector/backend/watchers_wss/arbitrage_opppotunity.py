import json
import time
from damexCommons.tools.exchange_db import ExchangeDB
from .base import WatcherWssBase

exchange_db = ExchangeDB(db_connection='exchange_connector')

WSS_ROUTE = 'arbitrage_opportunities'

class WatcherWssArbitrageOpportunities(WatcherWssBase):
    
    def __init__(self):
        folders_to_watch = ['../arbitrage_opportunities/simple', '../arbitrage_opportunities/triple']
        super().__init__(WSS_ROUTE, folders_to_watch=folders_to_watch, callback=self.callback)


    def callback(self, src_path: str, websocket_clients_to_send):
        try:
            time.sleep(0.1)
            data = open(src_path, 'r', encoding='UTF-8').read()
            parsed_data = json.loads(data)
            arbitrage_opportunities = {}
            for websocket_client_id in websocket_clients_to_send:
                operation = websocket_clients_to_send[websocket_client_id][2]
                match operation:
                    case 'fetch':
                        params = websocket_clients_to_send[websocket_client_id][1]
                        arbitrage_type = params['arbitrage_type']
                        if arbitrage_type not in src_path:
                            continue
                        if arbitrage_type not in arbitrage_opportunities:
                            arbitrage_opportunities[arbitrage_type] = []
                            for key in parsed_data:
                                init_time = parsed_data[key]['init_time']
                                last_time = parsed_data[key]['last_time']
                                if arbitrage_type == 'simple':
                                    arbitrage_opportunity = {
                                        'exchange_buy': key.split('__')[0],
                                        'exchange_sell': key.split('__')[1],
                                        'pair': key.split('__')[2],
                                        'init_time': init_time,
                                        'last_time': last_time,
                                        'period_in_secs': int((last_time - init_time) / 1e3),
                                        'profitability_percentage': parsed_data[key]['profitability_percentage'],
                                        'depth': parsed_data[key]['depth'],
                                        'profitability_amount': parsed_data[key]['profitability_amount'],
                                        'profitability_asset': parsed_data[key]['profitability_asset'],
                                    }
                                    if 'buy_price' in  parsed_data[key]:
                                        arbitrage_opportunity['buy_price'] = parsed_data[key]['buy_price']  
                                    if 'sell_price' in  parsed_data[key]:
                                        arbitrage_opportunity['sell_price'] = parsed_data[key]['sell_price']   
                                    arbitrage_opportunities[arbitrage_type].append(arbitrage_opportunity)
                                                                        
                                elif arbitrage_type == 'triple':
                                    arbitrage_opportunities[arbitrage_type].append({
                                        'exchange': key.split('__')[0],
                                        'pair_1': key.split('__')[1],
                                        'pair_2': key.split('__')[2],
                                        'pair_3': key.split('__')[3],
                                        'variation': parsed_data[key]['variation'],
                                        'init_time': init_time,
                                        'last_time': last_time,
                                        'period_in_secs': int((last_time - init_time) / 1e3),
                                        'profitability_percentage': parsed_data[key]['profitability_percentage'],
                                        'depth': parsed_data[key]['depth'],
                                        'profitability_amount': parsed_data[key]['profitability_amount'],
                                        'profitability_asset': parsed_data[key]['profitability_asset'],
                                    })
        
                        response = {
                            'id': websocket_client_id,
                            'operation': operation,
                            'params': params,
                            'type': 'new',
                            'data': arbitrage_opportunities[arbitrage_type]
                        }
                        print('------------', len(response['data']))
                        websocket_clients_to_send[websocket_client_id][0].send(text_data=json.dumps(response))
        except Exception as e:
            print('problem retrieving data', e)