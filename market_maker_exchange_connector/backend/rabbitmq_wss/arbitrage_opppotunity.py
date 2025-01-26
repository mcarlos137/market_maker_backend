import json
from .base import RabbitmqWssBase

WSS_ROUTE = 'arbitrage_opportunities'

class RabbitmqWssArbitrageOpportunities(RabbitmqWssBase):
    
    def __init__(self):
        super().__init__(WSS_ROUTE, callback=self.callback)


    def callback(self, data: dict, websocket_clients_to_send):
        try:
            arbitrage_opportunities = {}
            for websocket_client_id in websocket_clients_to_send:
                operation = websocket_clients_to_send[websocket_client_id][2]
                match operation:
                    case 'fetch':
                        params = websocket_clients_to_send[websocket_client_id][1]
                        arbitrage_type = params['arbitrage_type']
                        if arbitrage_type != 'simple':
                            continue
                        if arbitrage_type not in arbitrage_opportunities:
                            arbitrage_opportunities[arbitrage_type] = []
                            for key in data:
                                init_time = data[key]['init_time']
                                last_time = data[key]['last_time']
                                if arbitrage_type == 'simple':
                                    arbitrage_opportunity = {
                                        'exchange_buy': key.split('__')[0],
                                        'exchange_sell': key.split('__')[1],
                                        'pair': key.split('__')[2],
                                        'init_time': init_time,
                                        'last_time': last_time,
                                        'period_in_secs': int((last_time - init_time) / 1e3),
                                        'profitability_percentage': data[key]['profitability_percentage'],
                                        'depth': data[key]['depth'],
                                        'profitability_amount': data[key]['profitability_amount'],
                                        'profitability_asset': data[key]['profitability_asset'],
                                    }
                                    if 'buy_price' in  data[key]:
                                        arbitrage_opportunity['buy_price'] = data[key]['buy_price']  
                                    if 'sell_price' in  data[key]:
                                        arbitrage_opportunity['sell_price'] = data[key]['sell_price']   
                                    arbitrage_opportunities[arbitrage_type].append(arbitrage_opportunity)
                                                                        
                                elif arbitrage_type == 'triple':
                                    arbitrage_opportunities[arbitrage_type].append({
                                        'exchange': key.split('__')[0],
                                        'pair_1': key.split('__')[1],
                                        'pair_2': key.split('__')[2],
                                        'pair_3': key.split('__')[3],
                                        'variation': data[key]['variation'],
                                        'init_time': init_time,
                                        'last_time': last_time,
                                        'period_in_secs': int((last_time - init_time) / 1e3),
                                        'profitability_percentage': data[key]['profitability_percentage'],
                                        'depth': data[key]['depth'],
                                        'profitability_amount': data[key]['profitability_amount'],
                                        'profitability_asset': data[key]['profitability_asset'],
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