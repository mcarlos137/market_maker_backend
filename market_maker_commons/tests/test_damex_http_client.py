import asyncio
from damexCommons.tools.damex_http_client import get_main_price, change_bot_status, get_user_info, create_target_failed, fetch_emulated_balance, execute_emulated_balance

#def test_get_main_price():
#    main_price = asyncio.run(get_main_price(base_asset='DAMEX', quote_asset='USDT', price_decimals=5))
#    print('main_price', main_price)
#    assert False
    
#def test_change_bot_status():
#    change_bot_status_response = asyncio.run(change_bot_status(bot_id='12ffd', bot_type='vol', region='ireland', action='restart'))
#    print('change_bot_status', change_bot_status_response)
#    assert False
    
def test_get_user_info():
    user_info_response = asyncio.run(get_user_info())
    print('user_info_response', user_info_response)
    assert True

#def test_create_target_failed():
#    create_target_failed_response = asyncio.run(create_target_failed(target_id='34534'))
#    print('create_target_failed_response', create_target_failed_response)
#    assert False
    
def test_fetch_emulated_balance():
    fetch_emulated_balance_response = asyncio.run(fetch_emulated_balance(name='arbitrage_1_new'))
    print('fetch_emulated_balance_response', fetch_emulated_balance_response)
    assert False

''' 
def test_execute_emulated_balance():
    execute_emulated_balance_response = asyncio.run(execute_emulated_balance(
        name='arbitrage_1_new',
        exchange='tidex',
        asset='USDT',
        amount=155.0,
        operation='trade',
        asset_turn='SOL',
        amount_turn=1.0
    ))
    print('execute_emulated_balance_response', execute_emulated_balance_response)
    assert False
'''