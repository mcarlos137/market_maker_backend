import json
from .base import NotifierWssBase

WSS_ROUTE = 'order_books'

BASE_ASSET = 'DAMEX'
QUOTE_ASSET = 'USDT'

class NotifierWssOrderBooks(NotifierWssBase):
    
    def __init__(self):
        super().__init__(wss_route=WSS_ROUTE, notifier_id='notify_order_book_%s' % (BASE_ASSET.lower() + QUOTE_ASSET.lower()), callback=self.callback)

    def callback(self, data: dict, websocket_clients_to_send):
        try:
            fetch_data = {}
            get_price_data = {}
            for websocket_client_id in websocket_clients_to_send:
                operation = websocket_clients_to_send[websocket_client_id][2]
                params = websocket_clients_to_send[websocket_client_id][1]
                match operation:
                    case 'fetch':
                        size = params['size']
                        key = str(size)
                        if key not in fetch_data:
                            data['asks'] = data['asks'][0:size]
                            data['bids'] = data['bids'][0:size]
                            fetch_data[key] = data.copy()
                        response = {
                            'id': websocket_client_id,
                            'operation': operation,
                            'params': params,
                            'type': 'new',
                            'data': fetch_data[key]
                        }
                        print('----------------------------------------fetch', websocket_client_id, key)
                        websocket_clients_to_send[websocket_client_id][0].send(text_data=json.dumps(response))            
                    case 'get_price':
                        market = params['market']
                        amount = params['amount']
                        currency = params['currency']
                        side = params['side']
                        key = market + '__' + str(amount) + '__' + currency + '__' + side
                        if key not in get_price_data:
                            if len(data['bids']) == 0 and len(data['asks']) == 0 :
                                get_price_data[key] = {'price': None, 'amount': 0}   
                            if len(data['bids']) == 0 and len(data['asks']) > 0 and side == 'sell':
                                get_price_data[key] = {'price': data['asks'][0][0] * 0.95, 'amount': 0}
                            elif len(data['asks']) == 0 and len(data['bids']) > 0 and side == 'buy':
                                get_price_data[key] = {'price': data['bids'][0][0] * 1.05, 'amount': 0}
                            else:
                                market_components = market.split('-')
                                amount_left = amount
                                amount_by_price_sum = 0
                                for o in  data['bids' if side == 'sell' else 'asks']:  
                                    var = None
                                    if market_components[0] == currency:
                                        var = o[1]
                                    elif market_components[1] == currency:
                                        var = o[0] * o[1]
                                    if var >= amount_left:
                                        amount_by_price_sum += o[0] * amount_left
                                        amount_left = 0
                                        break 
                                    else:
                                        amount_by_price_sum += o[0] * var
                                        amount_left = amount_left - var
                                amount_new = amount - amount_left
                                if amount_new == 0:
                                    get_price_data[key] = {'price': None, 'amount': 0}
                                else:
                                    price = amount_by_price_sum / amount_new
                                    if side == 'sell' and len(data['asks']) > 0:
                                        ask_lowest_price = data['asks'][0][0]
                                        if float(price) > float(ask_lowest_price):
                                            price = ask_lowest_price
                                    get_price_data[key] = {'price': price, 'amount': amount_new}
                            
                        response = {
                            'id': websocket_client_id,
                            'operation': operation,
                            'params': params,
                            'type': 'new',
                            'data': get_price_data[key]
                        }
                        print('----------------------------------------get_price', websocket_client_id, key)
                        websocket_clients_to_send[websocket_client_id][0].send(text_data=json.dumps(response))   
                            
        except Exception as e:
            print('problem retrieving data', e)