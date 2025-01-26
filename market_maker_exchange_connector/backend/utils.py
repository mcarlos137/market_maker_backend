from datetime import datetime
from damexCommons.tools.utils import PERIODS, get_period_datetime

DATA_FOLDER = "../exchange_files"

DATA_OLD_FOLDER = "../exchange_files_old"

ROUTE_OPERATIONS = {
    'trades': {
        'fetch': {
            'params': ['market'],
            'folders': ['trades'],
            'datasets': None,
            'periods': None
        }
    },
    'order_books': {
        'fetch': {
            'params': ['market', 'size'],
            'folders': None,
            'datasets': None,
            'periods': None
        },
        'get_price': {
            'params': ['market', 'amount', 'currency', 'side'],
            'folders': None,
            'datasets': None,
            'periods': None
        }
    },
    'market_info': {
        'get': {
            'params': ['market'],
            'folders': ['ticker', 'order_books'],
            'datasets': None,
            'periods': None
        }
    },
    'current_orders': {
        'get_count': {
            'params': ['exchange', 'market', 'period', 'dataset', 'current_time', 'size'],
            'folders': ['current_orders_count'],
            'datasets': ['snap', 'incr', 'avg'],
            'periods': list(PERIODS.keys())
        },
        'get_amounts': {
            'params': ['exchange', 'market', 'period', 'dataset', 'current_time', 'size'],
            'folders': ['current_orders_amounts'],
            'datasets': ['snap', 'incr', 'avg'],
            'periods': list(PERIODS.keys())
        },
        'get_mid_prices': {
            'params': ['exchange', 'market', 'period', 'dataset', 'current_time', 'size'],
            'folders': ['current_orders_mid_prices'],
            'datasets': ['incr'],
            'periods': list(PERIODS.keys())
        }
    },
    'current_values': {
        'get': {
            'params': ['exchange', 'period', 'dataset', 'current_time', 'size'],
            'folders': ['current_values'],
            'datasets': ['snap'],
            'periods': list(PERIODS.keys())
        }
    },
    'current_spread': {
        'get': {
            'params': ['exchange', 'market', 'period', 'dataset', 'current_time', 'size'],
            'folders': ['order_books'],
            'datasets': ['snap'],
            'periods': list(PERIODS.keys())
        }
    },
    'arbitrage_opportunities': {
        'fetch': {
            'params': ['arbitrage_type'],
            'folders': None,
            'datasets': None,
            'periods': None
        }
    }
}

def get_new_file_time(file_time, period):
    selected_time = datetime.fromtimestamp(file_time / 1000)
    rounded_time = 0
    rounded_time = get_period_datetime(selected_time, period)
    if rounded_time == 0:
        return None
    new_file_time = int(rounded_time.timestamp() * 1000)
    return new_file_time

def get_minutes(period):
    match period:
        case '1m':
            return 1
        case '5m':
            return 5
        case '15m':
            return 15
        case '30m':
            return 30
        case '1h':
            return 60
        case '4h':
            return 240
        case '12h':
            return 720
        case '24h':
            return 1440
