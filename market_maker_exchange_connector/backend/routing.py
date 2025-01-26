from django.urls import re_path

from .consumers.exchange import ExchangeConsumer
from .consumers.exchange_api import ExchangeAPIConsumer
from .consumers.trades import ConsumerTrades
from .consumers.order_books import ConsumerOrderBooks
from .consumers.market_info import ConsumerMarketInfo
from .consumers.current_orders import ConsumerCurrentOrders
from .consumers.current_values import ConsumerCurrentValues
from .consumers.current_spread import ConsumerCurrentSpread
from .consumers.arbitrage_opportunity import ConsumerArbitrageOpportunities

websocket_urlpatterns = [
    re_path(r'ws/socket-server/exchange/', ExchangeConsumer.as_asgi()),
    re_path(r'ws/socket-server/exchange_api/', ExchangeAPIConsumer.as_asgi()),
    re_path(r'ws/socket-server/trades/', ConsumerTrades.as_asgi()),
    re_path(r'ws/socket-server/order_books/', ConsumerOrderBooks.as_asgi()),
    re_path(r'ws/socket-server/market_info/', ConsumerMarketInfo.as_asgi()),
    re_path(r'ws/socket-server/current_orders/', ConsumerCurrentOrders.as_asgi()),
    re_path(r'ws/socket-server/current_values/', ConsumerCurrentValues.as_asgi()),
    re_path(r'ws/socket-server/current_spread/', ConsumerCurrentSpread.as_asgi()),
    re_path(r'ws/socket-server/arbitrage_opportunities/', ConsumerArbitrageOpportunities.as_asgi()),
]