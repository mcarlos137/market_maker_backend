import base64
import datetime
import hashlib
import hmac
import json
from datetime import datetime, timezone
from typing import Optional
from damexCommons.tools.utils import http_request_damex

#BASE_URL = 'https://restmm.damex.io'
#BASE_URL = 'http://172.20.143.247:9000'
#BASE_URL = 'http://172.19.0.8:8001'
BASE_URL = 'http://10.132.0.4:8001'

async def get_main_price(base_asset: str, quote_asset: str, price_decimals: int) -> float:
    main_price = await http_request_damex(
        method='GET',
        url='%s/exchange_api/get_main_price?market=%s-%s' % (BASE_URL, base_asset, quote_asset),
        headers=get_headers(),
        retry=2
    )
    return round(float(main_price), price_decimals)

async def get_app_last_trade(base_asset: str, quote_asset: str) -> dict:
    app_last_trade = await http_request_damex(
        method='GET',
        url='%s/exchange_api/get_last_trade?market=%s-%s&source=APP' % (BASE_URL, base_asset, quote_asset),
        headers=get_headers(),
        retry=1
    )
    return app_last_trade
    
async def get_inventory_values(exchange: str, base_asset: str, quote_asset: str) -> dict:
    inventory_values = await http_request_damex(
        method='GET',
        url='%s/exchange_api/get_inventory_values?market=%s-%s&exchange=%s' % (BASE_URL, base_asset, quote_asset, exchange),
        headers=get_headers(),
        retry=1
    )
    return inventory_values

async def change_bot_status(bot_id: str, bot_type: str, region: str, action: str) -> None:
    data = {
        'bot_id': bot_id,
        'bot_type': bot_type,
        'region': region,
        'action': action,
    }
    await http_request_damex(
        method='POST',
        url='%s/bot/execute_action' % (BASE_URL),
        data=data,
        headers=get_headers(data),
        retry=2
    )
    
async def change_bot_strategy(bot_id: str, bot_type: str, region: str, strategy: str) -> None:
    data = {
        'bot_id': bot_id,
        'bot_type': bot_type,
        'region': region,
        'new_attributes_values': "{\"strategy\": \"" + strategy + "\"}"
    }
    await http_request_damex(
        method='POST',
        url='%s/bot/edit' % (BASE_URL),
        data=data,
        headers=get_headers(data),
        retry=2
    )
                
async def change_bot_target(bot_id: str, bot_type: str, region: str, target: str) -> None:
    data = {
        'bot_id': bot_id,
        'bot_type': bot_type,
        'region': region,
        'new_attributes_values': "{\"target\": \"" + target + "\"}"
    }
    await http_request_damex(
        method='POST',
        url='%s/bot/edit' % (BASE_URL),
        data=data,
        headers=get_headers(data),
        retry=2
    )
                
async def create_target(target_id: str, initial_timestamp: int, final_timestamp: int, asset: str, initial_asset_amount: float, operation: str, operation_amount: float) -> None:
    data = {
        'target_id': target_id,
        'initial_timestamp': initial_timestamp,
        'final_timestamp': final_timestamp,
        'asset': asset,
        'initial_asset_amount': initial_asset_amount,
        'operation': operation,
        'operation_amount': operation_amount
    }
    await http_request_damex(
        method='POST',
        url='%s/target/create' % (BASE_URL),
        data=data,
        headers=get_headers(data),
        retry=2
    )
        
async def create_target_failed(target_id: str) -> None:
    data = {
        'target_id': target_id,
    }
    await http_request_damex(
        method='POST',
        url='%s/target/create_failed' % (BASE_URL),
        data=data,
        headers=get_headers(data),
        retry=2
    )
        
async def fetch_target(target_id: str):
    target = await http_request_damex(
        method='GET',
        url='%s/target/fetch?target_id=%s' % (BASE_URL, target_id),
        headers=get_headers(),
        retry=1
    )
    return target

async def update_target(target_id: str, status: str) -> None:
    data = {
        'target_id': target_id,
        'new_attributes_values': "{\"status\": \"%s\"}" % (status)
    }
    await http_request_damex(
        method='POST',
        url='%s/target/edit' % (BASE_URL),
        data=data,
        headers=get_headers(data),
        retry=2
    )
    
async def get_bot_strategy(bot_id: str, bot_type: str) -> str:
    print('-------', '%s/bot/get_strategy' % (BASE_URL))
    return await http_request_damex(
        method='GET',
        url='%s/bot/get_strategy?bot_type=%s&bot_id=%s' % (BASE_URL, bot_type, bot_id),
        headers=get_headers(),
    )
    
async def get_user_info() -> dict:
    print('-------', '%s/user/get_info' % (BASE_URL))
    return await http_request_damex(
        method='GET',
        url='%s/user/get_info' % (BASE_URL),
        headers=get_headers(),
        retry=1
    )
    
async def fetch_emulated_balance(name: str) -> dict:
    print('-------', '%s/emulated_balance/fetch' % (BASE_URL))
    return await http_request_damex(
        method='GET',
        url='%s/emulated_balance/fetch?name=%s&type=current' % (BASE_URL, name),
        headers=get_headers(),
        retry=1
    )
    
async def execute_emulated_balance(name: str, exchange: str, asset: str, amount: float, operation: str, asset_turn: Optional[str] = None, amount_turn: Optional[float] = None) -> dict:
    data = {
        'name': name,
        'exchange': exchange,
        'asset': asset,
        'amount': amount,
        'operation': operation,
    }
    if asset_turn is not None:
        data['asset_turn'] = asset_turn
    if amount_turn is not None:
        data['amount_turn'] = amount_turn
    await http_request_damex(
        method='POST',
        url='%s/emulated_balance/execute' % (BASE_URL),
        data=data,
        headers=get_headers(data),
        retry=2
    )
    
###################    
async def fetch_emulated_balance_new(name: str) -> dict:
    print('-------', '%s/emulated_balance_new/fetch' % (BASE_URL))
    return await http_request_damex(
        method='GET',
        url='%s/emulated_balance_new/fetch?name=%s&type=current' % (BASE_URL, name),
        headers=get_headers(),
        retry=1
    )
    
async def execute_emulated_balance_new(name: str, exchange: str, asset: str, amount: float, operation: str, asset_turn: Optional[str] = None, amount_turn: Optional[float] = None) -> dict:
    data = {
        'name': name,
        'exchange': exchange,
        'asset': asset,
        'amount': amount,
        'operation': operation,
    }
    if asset_turn is not None:
        data['asset_turn'] = asset_turn
    if amount_turn is not None:
        data['amount_turn'] = amount_turn
    await http_request_damex(
        method='POST',
        url='%s/emulated_balance_new/execute' % (BASE_URL),
        data=data,
        headers=get_headers(data),
        retry=2
    )
###################
    
API_KEY = '23fff5c3-93a9-4196-ab56-e940383be945'
API_SECRET = 'pamiH/kfP3WcXFHM/MXSc3y6pBCaUs0bpwyhYdKI62A='

digests_map = {
    'HMAC-SHA512': hashlib.sha512,
    'HMAC-SHA384': hashlib.sha384,
    'HMAC-SHA256': hashlib.sha256,
}

def _hash_content(digest: str, content: bytes):
    if not content:
        return None
    if digest not in digests_map.keys():
        raise ValueError(f'Unsupported HMAC function {digest}')
    func = digests_map[digest]
    hasher = func()
    hasher.update(content)
    hashed_bytes = hasher.digest()
    base64_encoded_bytes = base64.b64encode(hashed_bytes)
    content_hash = base64_encoded_bytes.decode('UTF-8')
    return content_hash


def _prepare_string_to_sign(data: dict, utc_8601: str, digest: str):
    body = (
        None if not data else json.dumps(data, separators=(',', ':')).encode('UTF-8')
    )
    body_hash = _hash_content(digest, body)
    string_to_sign = f';{utc_8601}'

    if body_hash:
        string_to_sign = f'{body_hash}' + string_to_sign
    return string_to_sign

def _sign_string(string_to_sign: str, secret: bytes, digest):
    if digest not in digests_map.keys():
        raise ValueError(f'Unsupported HMAC function {digest}')
    encoded_string_to_sign = string_to_sign.encode('UTF-8')
    hashed_bytes = hmac.digest(
        secret, encoded_string_to_sign, digest=digests_map[digest]
    )
    encoded_signature = base64.b64encode(hashed_bytes)
    signature = encoded_signature.decode('UTF-8')
    return signature

def get_headers(body: dict = None):
    api_secret = base64.b64decode(API_SECRET)
    digest = 'HMAC-SHA512'
    utc_8601 = (
        datetime.utcnow().replace(tzinfo=timezone.utc).isoformat()
    )
    string_to_sign = _prepare_string_to_sign(body, utc_8601, digest)
    signature = _sign_string(string_to_sign, api_secret, digest)
    authorization_header = f'{digest} {API_KEY};{signature};{utc_8601}'
    
    headers = {
        'Authorization': authorization_header,
        'Content-Type': 'application/json',
    }
    return headers