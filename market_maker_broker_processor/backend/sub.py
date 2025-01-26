import os
import json
from datetime import datetime
from commlib.msg import PubSubMessage
from commlib.transports.mqtt import (
    ConnectionParameters, PSubscriber
)
from django.db import connection
import uuid


class SubMessage(PubSubMessage):
    distance: float = 0.001
    horizontal_fov: float = 30.0
    vertical_fov: float = 14.0

    def main(args):
        conn_params = ConnectionParameters(
            host='localhost', port=1883, username='mqtt-test', password='mqtt-test')
        instance_id = args[0]
        source = args[1]
        sub = PSubscriber(topic='hbot/' + instance_id + '/' + source,
                          on_message=hb_data_callback,
                          conn_params=conn_params)
        sub.run()


def hb_data_callback(msg, topic):
    print('----------------------------------------------------------------')
    instance_id = topic.split('/')[1]
    source = topic.split('/')[2]
    object = Object(msg)
    console_log = str(msg)
    print(console_log)
    console_log_instance_folder = '../console_log_files/' + instance_id + '/'
    if not os.path.exists(console_log_instance_folder):
        os.makedirs(console_log_instance_folder)
    f = open(console_log_instance_folder + str(uuid.uuid4()) + '.log', 'w+')
    f.write(console_log)
    f.close()
    print('----------------------------------------------------------------')
    match source:
        case 'events':
            match object.type:
                case 'SellOrderCreated':
                    create_order(instance_id, object.data['trading_pair'].split('-')[0],
                                 object.data['trading_pair'].split('-')[1], 2, 1, 1, object.data['price'], object.data['amount'], object.data['order_id'])
                case 'BuyOrderCreated':
                    create_order(instance_id, object.data['trading_pair'].split('-')[0],
                                 object.data['trading_pair'].split('-')[1], 1, 1, 1, object.data['price'], object.data['amount'], object.data['order_id'])
                case 'OrderCancelled':
                    cancel_order(object.data['order_id'])
                case 'BuyOrderCompleted' | 'SellOrderCompleted':
                    complete_order(object.data['order_id'])
                case _:
                    print("%s" % (msg))
        case 'hb':
            print("ts: %s" % (object.ts))
        case 'notify':
            action = ''
            if "Markets:" in object.msg and "Assets:" in object.msg and "Orders:" in object.msg:
                action = 'status_pure_mm'
            elif "Order price:" in object.msg:
                action = 'status_twap'
            elif "Trades:" in object.msg:
                action = 'history'
            if action is not '':
                notify = process_notify(str(object.msg), action)
                print('notify ' + str(action) + ' ' + str(notify))
                f = open('../%s_files/' % (action.split('_')[0]) + instance_id + '.txt', 'w+')
                f.write(json.dumps(object.msg))
                f.close()
                if action is 'history':
                    add_history(notify, instance_id)
                elif action is 'status_pure_mm':
                    add_status_pure_mm(notify, instance_id)
            else:
                print("-------------------: %s" % (msg))

def create_order(instance_id, asset_base, asset_quote, side, status, type, price, amount, order_id):
    cursor = connection.cursor()
    query = "SELECT id, exchange_id, finished_at FROM %s WHERE instance_id='%s' ORDER BY id DESC LIMIT 1;" % ('"BOT_SPRINTS"', instance_id)
    print(query)
    cursor.execute(query)
    row = cursor.fetchall()
    if row:
        if row[0][2] is None:
            exchange_id = row[0][1]
            # asset_base = 'BTC'
            # asset_quote = 'USDT'
            # side = 1
            # status = 1
            # type = 1
            # price = 24503.3
            # amount = 0.3
            bot_sprint_id = row[0][0]
            query = "INSERT INTO %s (exchange_id, market_id, side, status, type, price, amount, bot_sprint_id, hummingbot_order_id) VALUES (%s, (SELECT id FROM %s WHERE base='%s' AND quote='%s'), %s, %s, %s, %s, %s, %s, '%s');" % (
                '"ORDERS"', exchange_id, '"MARKETS"', asset_base, asset_quote, side, status, type, price, amount, bot_sprint_id, order_id)
            print(query)
            cursor.execute(query)
            connection.commit()
            
        else:
            print('NO RESULTS')
    connection.close()


def cancel_order(order_id):
    cursor = connection.cursor()
    query = "UPDATE %s SET status = 2 WHERE hummingbot_order_id='%s'" % ('"ORDERS"', order_id)
    print(query)
    cursor.execute(query)
    connection.commit()
    connection.close()


def complete_order(order_id):
    cursor = connection.cursor()
    query = "UPDATE %s SET status = 3 WHERE hummingbot_order_id='%s'" % ('"ORDERS"', order_id)
    print(query)
    cursor.execute(query)
    connection.commit()
    connection.close()

def add_history(history, instance_id):
    cursor = connection.cursor()
    query = "SELECT id, finished_at FROM %s WHERE instance_id='%s' ORDER BY id DESC LIMIT 1;" % ('"BOT_SPRINTS"', instance_id)
    print(query)
    cursor.execute(query)
    row = cursor.fetchall()
    if row:
        if row[0][1] is None:
            bot_sprint_id = row[0][0]
            query = "INSERT INTO %s (bot_sprint_id, trades_number_buy, trades_number_sell, trades_number_total, trade_volume_base_buy, trade_volume_base_sell, trade_volume_base_total, trade_volume_quote_buy, trade_volume_quote_sell, trade_volume_quote_total, price_avg_buy, price_avg_sell, price_avg_total, assets_base_start, assets_base_current, assets_base_change, assets_quote_start, assets_quote_current, assets_quote_change, price_start, price_current, price_change, assets_base_percent_start, assets_base_percent_current, assets_base_percent_change, portfolio_hold_quote, portfolio_current_quote, trade_pl_quote, fees_paid_quote, total_pl_quote, return_percent) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);" % (
                '"BOT_HISTORIES"', bot_sprint_id, history['trades_number']['buy'], history['trades_number']['sell'], history['trades_number']['total'], history['trade_volume_base']['buy'], history['trade_volume_base']['sell'], history['trade_volume_base']['total'], history['trade_volume_quote']['buy'], history['trade_volume_quote']['sell'], history['trade_volume_quote']['total'], history['price']['avg']['buy'], history['price']['avg']['sell'], history['price']['avg']['total'], history['assets']['base']['start'], history['assets']['base']['current'], history['assets']['base']['change'], history['assets']['quote']['start'], history['assets']['quote']['current'], history['assets']['quote']['change'], history['price']['start'], history['price']['current'], history['price']['change'], history['assets']['base']['percent']['start'], history['assets']['base']['percent']['current'], history['assets']['base']['percent']['change'], history['portfolio']['hold_quote'], history['portfolio']['current_quote'], history['trade_pl_quote'], history['fees_paid_quote'], history['total_pl_quote'], history['return_percent'])
            
            print('-----------------------------------')
            print(query)
            print('-----------------------------------')
            cursor.execute(query)
            connection.commit()
    connection.close()
        
def add_status_pure_mm(status, instance_id):
    cursor = connection.cursor()
    query = "SELECT id, finished_at FROM %s WHERE instance_id='%s' ORDER BY id DESC LIMIT 1;" % ('"BOT_SPRINTS"', instance_id)
    print(query)
    cursor.execute(query)
    row = cursor.fetchall()
    if row:
        if row[0][1] is None:
            bot_sprint_id = row[0][0]
            query = "INSERT INTO %s (bot_sprint_id, price_bid_best, price_ask_best, price_mid, balance_total_base, balance_total_quote, balance_available_base, balance_available_quote, current_value_quote_base, current_value_quote_quote, current_percent_base, current_percent_quote, order_levels) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);" % (
                '"BOT_STATUSES"', bot_sprint_id, status['price']['bid_best'], status['price']['ask_best'], status['price']['mid'], status['balance']['total']['base'], status['balance']['total']['quote'], status['balance']['available']['base'], status['balance']['available']['quote'], status['current']['value_quote']['base'], status['current']['value_quote']['quote'], status['current']['percent']['base'], status['current']['percent']['quote'], '"[]"')
            print('-----------------------------------')
            print(query)
            print('-----------------------------------')
            cursor.execute(query)
            connection.commit()
    connection.close()
    #order_levels

class Object:
    def __init__(self, d=None):
        if d is not None:
            for key, value in d.items():
                setattr(self, key, value)
                
def get_hummingbot_connector(exchange):
    match exchange:
        case 'kucoin_PaperTrade':
            return 'kucoin_paper_trade'
                
def process_notify(string, type):
    line_number = 0
    result = {}
    if type is 'status_pure_mm':
        result['order_levels'] = []
    for line in string.splitlines():
        line = ' '.join(line.split())
        match(type):
            case 'history':
                match(line_number):
                    case 0 | 2 | 3 | 4 | 9 | 10 | 11 | 16 | 17:
                        pass
                    case 1:
                        result['hummingbot_connector'] = get_hummingbot_connector(line.split(' / ')[0])
                        result['market'] = line.split(' / ')[1]
                        result['asset'] = {
                            'base': result['market'].split('-')[0],
                            'quote': result['market'].split('-')[1]
                        }
                    case 5:
                        replace_string = 'Number of trades '
                        result['trades_number'] = {
                            'buy': int(line.strip().replace(replace_string, '').split(' ')[0]),
                            'sell': int(line.strip().replace(replace_string, '').split(' ')[1]),
                            'total': int(line.strip().replace(replace_string, '').split(' ')[2])
                        }
                    case 6:
                        replace_string = 'Total trade volume (%s) ' % (
                            result['asset']['base'])
                        result['trade_volume_base'] = {
                            'buy': float(line.strip().replace(replace_string, '').split(' ')[0]),
                            'sell': float(line.strip().replace(replace_string, '').split(' ')[1]),
                            'total': float(line.strip().replace(replace_string, '').split(' ')[2])
                        }
                    case 7:
                        replace_string = 'Total trade volume (%s) ' % (
                            result['asset']['quote'])
                        result['trade_volume_quote'] = {
                            'buy': float(line.strip().replace(replace_string, '').split(' ')[0]),
                            'sell': float(line.strip().replace(replace_string, '').split(' ')[1]),
                            'total': float(line.strip().replace(replace_string, '').split(' ')[2])
                        }
                    case 8:
                        replace_string = 'Avg price '
                        result['price'] = {
                            'avg': {
                                'buy': float(line.strip().replace(replace_string, '').split(' ')[0]),
                                'sell': float(line.strip().replace(replace_string, '').split(' ')[1]),
                                'total': float(line.strip().replace(replace_string, '').split(' ')[2])                                
                            }
                        }
                    case 12:
                        replace_string = '%s ' % (result['asset']['base'])
                        result['assets'] = {
                            'base': {
                                'start': float(line.strip().replace(replace_string, '').split(' ')[0]),
                                'current': float(line.strip().replace(replace_string, '').split(' ')[1]),
                                'change': float(line.strip().replace(replace_string, '').split(' ')[2])
                            }
                        }
                    case 13:
                        replace_string = '%s ' % (result['asset']['quote'])
                        result['assets']['quote'] = {
                            'start': float(line.strip().replace(replace_string, '').split(' ')[0]),
                            'current': float(line.strip().replace(replace_string, '').split(' ')[1]),
                            'change': float(line.strip().replace(replace_string, '').split(' ')[2])
                        }
                    case 14:
                        replace_string = '%s price ' % (result['market'])
                        result['price'] = {
                            'avg': result['price']['avg'],
                            'start': float(line.strip().replace(replace_string, '').split(' ')[0]),
                            'current': float(line.strip().replace(replace_string, '').split(' ')[1]),
                            'change': float(line.strip().replace(replace_string, '').split(' ')[2])
                        }
                    case 15:
                        replace_string = 'Base asset % '
                        result['assets']['base']['percent'] = {
                            'start': float(line.strip().replace(replace_string, '').split(' ')[0].replace('%', '')),
                            'current': float(line.strip().replace(replace_string, '').split(' ')[1].replace('%', '')),
                            'change': float(line.strip().replace(replace_string, '').split(' ')[2].replace('%', ''))
                        }
                    case 18:
                        replace_string_1 = 'Hold portfolio value '
                        replace_string_2 = ' %s' % (result['asset']['quote'])
                        portfolio_hold_quote = line.replace(replace_string_1, '').replace(replace_string_2, '')
                        result['portfolio'] = {
                            'hold_quote': float(portfolio_hold_quote)
                        }
                    case 19:
                        replace_string_1 = 'Current portfolio value '
                        replace_string_2 = ' %s' % (result['asset']['quote'])
                        portfolio_current_quote = line.replace(
                            replace_string_1, '').replace(replace_string_2, '')
                        result['portfolio']['current_quote'] = float(
                            portfolio_current_quote)
                    case 20:
                        replace_string_1 = 'Trade P&L '
                        replace_string_2 = ' %s' % (result['asset']['quote'])
                        trade_pl_quote = line.replace(
                            replace_string_1, '').replace(replace_string_2, '')
                        result['trade_pl_quote'] = float(trade_pl_quote)
                    case 21:
                        replace_string_1 = 'Fees paid '
                        replace_string_2 = ' %s' % (result['asset']['quote'])
                        fees_paid_quote = line.replace(
                            replace_string_1, '').replace(replace_string_2, '')
                        result['fees_paid_quote'] = float(fees_paid_quote)
                    case 22:
                        replace_string_1 = 'Total P&L '
                        replace_string_2 = ' %s' % (result['asset']['quote'])
                        total_pl_quote = line.replace(
                            replace_string_1, '').replace(replace_string_2, '')
                        result['total_pl_quote'] = float(total_pl_quote)
                    case 23:
                        replace_string_1 = 'Return % '
                        return_percent = line.replace(
                            replace_string_1, '').replace('%', '')
                        result['return_percent'] = float(return_percent)
                    case _:
                        print(line_number)
                        print(line)
            case 'status_pure_mm' | 'status_avellaneda_mm':
                match(line_number):
                    case 0 | 1 | 2 | 3 | 4 | 6 | 7 | 8 | 13 | 14 | 15:
                        pass
                    case 5:
                        result['hummingbot_connector'] = get_hummingbot_connector(str(line.strip().split(' ')[0]))
                        result['market'] = str(line.strip().split(' ')[1])
                        result['asset'] = {
                            'base': result['market'].split('-')[0],
                            'quote': result['market'].split('-')[1]
                        }
                        result['price'] = {
                            'bid_best': float(line.strip().split(' ')[2]),
                            'ask_best': float(line.strip().split(' ')[3]),
                            'mid': float(line.strip().split(' ')[4])
                        }
                        if type is 'status_avellaneda_mm':
                            result['price'] = {
                                'reservation': float(line.strip().split(' ')[5]),
                                'optimal_spread': float(line.strip().split(' ')[6])
                            }
                    case 9:
                        replace_string = 'Total Balance '
                        result['balance'] = {
                            'total': {
                                'base': float(line.strip().replace(replace_string, '').split(' ')[0]),
                                'quote': float(line.strip().replace(replace_string, '').split(' ')[1])
                            }
                        }
                    case 10:
                        replace_string = 'Available Balance '
                        result['balance']['available'] = {
                            'base': float(line.strip().replace(replace_string, '').split(' ')[0]),
                            'quote': float(line.strip().replace(replace_string, '').split(' ')[1])
                        }
                    case 11:
                        replace_string = 'Current Value (%s) ' % (
                            result['asset']['quote'])
                        result['current'] = {
                            'value_quote': {
                                'base': float(line.strip().replace(replace_string, '').split(' ')[0]),
                                'quote': float(line.strip().replace(replace_string, '').split(' ')[1])
                            }
                        }
                    case 12:
                        replace_string = 'Current % '
                        result['current']['percent'] = {
                            'base': float(line.strip().replace(replace_string, '').split(' ')[0].replace('%', '')),
                            'quote': float(line.strip().replace(replace_string, '').split(' ')[1].replace('%', ''))
                        }
                    case _:
                        if line == '':
                            continue
                        if 'Strategy parameters:' in line:
                            break
                        order = {
                            'level': str(line.strip().split(' ')[0]),
                            'type': str(line.strip().split(' ')[1]),
                            'price': float(line.strip().split(' ')[2]),
                            'spread_percent': float(line.strip().split(' ')[3].replace('%', '')),
                            'amount': {
                                'orig': float(line.strip().split(' ')[4]),
                                'adj': float(line.strip().split(' ')[5]),
                            },
                            'age': str(line.strip().split(' ')[6])
                        }
                        result['order_levels'].append(order)
        line_number = line_number + 1
    return result

