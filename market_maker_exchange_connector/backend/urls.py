from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
from .models.user import UserViewSet
from .views.exchange import reset_pnl_accumulated, get_apis, get_api_params, add_api, change_default_api, get_wallets, get_treasury_overview
from .views.exchange_api import post_trade, get_order_book, get_main_price, get_trades, get_inventory_values, get_last_trade, get_balance_resume

from .views.orchestrarion_rule import create as orchestrarion_rule_create, edit as orchestrarion_rule_edit, execute_action as orchestrarion_rule_execute_action, fetch as orchestrarion_rule_fetch, get_status as orchestrarion_rule_get_status, fetch_target_params as orchestrarion_rule_fetch_target_params, edit_target as orchestrarion_rule_edit_target, add_rule as orchestrarion_rule_add_rule, remove_rule as orchestrarion_rule_remove_rule, fetch_rule_actions as orchestrarion_rule_fetch_rule_actions, edit_rules as orchestrarion_rule_edit_rules, fetch_available_strategies as orchestrarion_rule_fetch_available_strategies, fetch_available_rule_actions as orchestrarion_rule_fetch_available_rule_actions
from .views.bot import create as bot_create, edit as bot_edit, execute_action as bot_execute_action, fetch as bot_fetch, get_status as bot_get_status, get_trades as bot_get_trades, get_volume as bot_get_volume, fetch_trades as bot_fetch_trades, get_strategy as bot_get_strategy
from .views.strategy import create as strategy_create, edit as strategy_edit, fetch as strategy_fetch, fetch_params as strategy_fetch_params
from .views.target import create as target_create, create_failed as target_create_failed, edit as target_edit, fetch as target_fetch
from .views.bot_multi_source import create as bot_multi_source_create
from .views.emulated_balance import add as emulated_balance_add, execute as emulated_balance_execute, fetch as emulated_balance_fetch, reset as emulated_balance_reset
from .views.emulated_balance_new import add as emulated_balance_new_add, execute as emulated_balance_new_execute, fetch as emulated_balance_new_fetch, reset as emulated_balance_new_reset, evaluate_trades as emulated_balance_new_evaluate_trades, get_process_data as emulated_balance_new_get_process_data

from .views.arbitrage_opportunity import fetch as arbitrage_opportunity_fetch


from .views.dex import get_liquidity_pools as dex_get_liquidity_pools

from .views.user import get_info as user_get_info

from .views.exchange_api_testing import get_last_price as get_last_price_testing, post_trade as post_trade_testing

from django_hmac_authentication.views import CreateApiHMACKey
from django_otp.admin import OTPAdminSite


router = routers.DefaultRouter()
router.register(r'users', UserViewSet)

admin.site.__class__ = OTPAdminSite

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include(router.urls)),
    path('api-auth/', include('rest_framework.urls')),
    path('obtain-hmac-api-key/', CreateApiHMACKey.as_view(), name='api_hmac_key'),
        
    path('exchange/get_apis', get_apis),
    path('exchange/get_api_params', get_api_params),    
    path('exchange/add_api', add_api),
    path('exchange/change_default_api', change_default_api),
    path('exchange/get_wallets', get_wallets),
    path('exchange/get_treasury_overview', get_treasury_overview),
    path('exchange/reset_pnl_accumulated', reset_pnl_accumulated),
    
    path('exchange_api/get_order_book', get_order_book),
    path('exchange_api/get_main_price', get_main_price),
    path('exchange_api/post_trade', post_trade),
    path('exchange_api/get_trades', get_trades),
    path('exchange_api/get_last_trade', get_last_trade),
    path('exchange_api/get_inventory_values', get_inventory_values),
    path('exchange_api/get_balance_resume', get_balance_resume),
    path('exchange_api_testing/get_last_price', get_last_price_testing),
    path('exchange_api_testing/post_trade', post_trade_testing),
        
    path('orchestration_rule/create', orchestrarion_rule_create),
    path('orchestration_rule/edit', orchestrarion_rule_edit),
    path('orchestration_rule/execute_action', orchestrarion_rule_execute_action),
    path('orchestration_rule/get_status', orchestrarion_rule_get_status),
    path('orchestration_rule/fetch', orchestrarion_rule_fetch),
    path('orchestration_rule/fetch_target_params', orchestrarion_rule_fetch_target_params),
    path('orchestration_rule/edit_target', orchestrarion_rule_edit_target),
    path('orchestration_rule/add_rule', orchestrarion_rule_add_rule),
    path('orchestration_rule/remove_rule', orchestrarion_rule_remove_rule),
    path('orchestration_rule/fetch_rule_actions', orchestrarion_rule_fetch_rule_actions),
    path('orchestration_rule/edit_rules', orchestrarion_rule_edit_rules),
    path('orchestration_rule/fetch_available_strategies', orchestrarion_rule_fetch_available_strategies),
    path('orchestration_rule/fetch_available_rule_actions', orchestrarion_rule_fetch_available_rule_actions),
    
    path('bot/create', bot_create),
    path('bot/edit', bot_edit),
    path('bot/execute_action', bot_execute_action),
    path('bot/get_status', bot_get_status),
    path('bot/fetch', bot_fetch),
    path('bot/get_volume', bot_get_volume),
    path('bot/get_trades', bot_get_trades),
    path('bot/fetch_trades', bot_fetch_trades),
    path('bot/get_strategy', bot_get_strategy),
    
    path('bot_multi_source/create', bot_multi_source_create),
    
    path('emulated_balance/add', emulated_balance_add),
    path('emulated_balance/execute', emulated_balance_execute),
    path('emulated_balance/fetch', emulated_balance_fetch),
    path('emulated_balance/reset', emulated_balance_reset),
    
    path('emulated_balance_new/add', emulated_balance_new_add),
    path('emulated_balance_new/execute', emulated_balance_new_execute),
    path('emulated_balance_new/fetch', emulated_balance_new_fetch),
    path('emulated_balance_new/reset', emulated_balance_new_reset),
    path('emulated_balance_new/evaluate_trades', emulated_balance_new_evaluate_trades),
    path('emulated_balance_new/get_process_data', emulated_balance_new_get_process_data),
    
    path('strategy/create', strategy_create),
    path('strategy/edit', strategy_edit),
    path('strategy/fetch', strategy_fetch),
    path('strategy/fetch_params', strategy_fetch_params),
    
    path('target/create', target_create),
    path('target/create_failed', target_create_failed),
    path('target/edit', target_edit),
    path('target/fetch', target_fetch),
    
    path('arbitrage_opportunity/fetch', arbitrage_opportunity_fetch),
    
    path('dex/get_liquidity_pools', dex_get_liquidity_pools),
    
    path('user/get_info', user_get_info),
    
]
