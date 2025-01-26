import json
import ccxt
from damexCommons.connectors.bitmart import BitmartCommons
from damexCommons.connectors.ascendex import AscendexCommons
from damexCommons.connectors.mexc import MexcCommons
from damexCommons.connectors.binance import BinanceCommons
from damexCommons.connectors.bitstamp import BitstampCommons
from damexCommons.connectors.gateio import GateioCommons
from damexCommons.connectors.coinstore import CoinstoreCommons
from damexCommons.connectors.tidex import TidexCommons
from damexCommons.connectors.hitbtc import HitbtcCommons
from damexCommons.connectors.bitfinex import BitfinexCommons
from damexCommons.connectors.kucoin import KucoinCommons
from damexCommons.connectors.coinex import CoinexCommons
from damexCommons.connectors.okcoin import OkcoinCommons
from damexCommons.connectors.kraken import KrakenCommons
from damexCommons.connectors.gemini import GeminiCommons
from damexCommons.connectors.lmax import LmaxCommons
from damexCommons.connectors.bitvavo import BitvavoCommons
from damexCommons.connectors.cryptocom import CryptocomCommons
from damexCommons.connectors.coinbase import CoinbaseCommons
from damexCommons.connectors.gateway import GatewayCommons
from damexCommons.connectors.raydium import RaydiumCommons
from damexCommons.connectors.b2c2 import B2C2Commons

EXCHANGES = [
    'bitmart',
    'mexc',
    'ascendex',
    'binance',
    'coinex',
    'gateio',
    'bitfinex',
    'bitstamp',
    'kucoin',
    'coinstore',
    'tidex',
    'tidex_new',
    'b2c2',
    'hitbtc',
    'okcoin',
    'kraken',
    'gemini',
    'lmax',
    'bitvavo',
    'cryptocom',
    'coinbase'
]

CONNECTORS = [
    'uniswap',
    'raydium',
    'jupiter'
]

def get_commons(base_asset: str, quote_asset: str, exchange_or_connector: str, api_or_wallet: str):
    commons = None
    if exchange_or_connector in EXCHANGES:
        with open('/mnt/data/apis_new.json', encoding='UTF-8') as f:
            apis = json.load(f)
            match exchange_or_connector:
                case 'bitmart':
                    commons = BitmartCommons(exchange_connector=ccxt.bitmart({
                        'apiKey': apis[api_or_wallet][0]['api_key'],
                        'secret': apis[api_or_wallet][0]['api_secret'],
                        'uid': apis[api_or_wallet][0]['api_memo']
                    }), base_asset=base_asset, quote_asset=quote_asset)
                case 'mexc':
                    commons = MexcCommons(exchange_connector=ccxt.mexc({
                        'apiKey': apis[api_or_wallet][0]['api_key'],
                        'secret': apis[api_or_wallet][0]['api_secret']
                    }), base_asset=base_asset, quote_asset=quote_asset)
                case 'ascendex':
                    commons = AscendexCommons(exchange_connector=ccxt.ascendex({
                        'apiKey': apis[api_or_wallet][0]['api_key'],
                        'secret': apis[api_or_wallet][0]['api_secret']
                    }), base_asset=base_asset, quote_asset=quote_asset)
                case 'binance':
                    commons = BinanceCommons(exchange_connector=ccxt.binance({
                        'apiKey': apis[api_or_wallet][0]['api_key'],
                        'secret': apis[api_or_wallet][0]['api_secret']
                    }), base_asset=base_asset, quote_asset=quote_asset)
                case 'gateio':
                    commons = GateioCommons(exchange_connector=ccxt.gateio({
                        'apiKey': apis[api_or_wallet][0]['api_key'],
                        'secret': apis[api_or_wallet][0]['api_secret']
                    }), base_asset=base_asset, quote_asset=quote_asset)
                case 'bitstamp':
                    commons = BitstampCommons(exchange_connector=ccxt.bitstamp({
                        'apiKey': apis[api_or_wallet][0]['api_key'],
                        'secret': apis[api_or_wallet][0]['api_secret']
                    }), base_asset=base_asset, quote_asset=quote_asset)
                case 'bitfinex':
                    commons = BitfinexCommons(exchange_connector=ccxt.bitfinex2({
                        'apiKey': apis[api_or_wallet][0]['api_key'],
                        'secret': apis[api_or_wallet][0]['api_secret']
                    }), base_asset=base_asset, quote_asset=quote_asset)
                case 'tidex':
                    commons = TidexCommons(
                        api_key=apis[api_or_wallet][0]['api_key'], 
                        api_secret=apis[api_or_wallet][0]['api_secret'], 
                        base_asset=base_asset, quote_asset=quote_asset)
                case 'hitbtc':
                    commons = HitbtcCommons(exchange_connector=ccxt.hitbtc({
                        'apiKey': apis[api_or_wallet][0]['api_key'],
                        'secret': apis[api_or_wallet][0]['api_secret']
                    }), base_asset=base_asset, quote_asset=quote_asset)
                case 'okcoin':
                    commons = OkcoinCommons(exchange_connector=ccxt.okcoin({
                        'apiKey': apis[api_or_wallet][0]['api_key'],
                        'secret': apis[api_or_wallet][0]['api_secret']
                    }), base_asset=base_asset, quote_asset=quote_asset)
                case 'kraken':
                    commons = KrakenCommons(exchange_connector=ccxt.kraken({
                        'apiKey': apis[api_or_wallet][0]['api_key'],
                        'secret': apis[api_or_wallet][0]['api_secret']
                    }), base_asset=base_asset, quote_asset=quote_asset)
                case 'gemini':
                    commons = GeminiCommons(exchange_connector=ccxt.gemini({
                        'apiKey': apis[api_or_wallet][0]['api_key'],
                        'secret': apis[api_or_wallet][0]['api_secret']
                    }), base_asset=base_asset, quote_asset=quote_asset)
                #case 'tidex_new':
                #    commons = TidexNewCommons(exchange_connector=ccxt.tidex({
                #        'apiKey': apis[api_or_wallet]['api_key'],
                #        'secret': apis[api_or_wallet]['api_secret']
                #    }), base_asset=base_asset, quote_asset=quote_asset)
                case 'kucoin':
                    commons = KucoinCommons(exchange_connector=ccxt.kucoin({
                        'apiKey': apis[api_or_wallet][0]['api_key'],
                        'secret': apis[api_or_wallet][0]['api_secret'],
                        'password': apis[api_or_wallet][0]['api_passphrase']
                    }), base_asset=base_asset, quote_asset=quote_asset)
                case 'coinex':
                    commons = CoinexCommons(exchange_connector=ccxt.coinex({
                        'apiKey': apis[api_or_wallet][0]['api_key'],
                        'secret': apis[api_or_wallet][0]['api_secret'],
                    }), base_asset=base_asset, quote_asset=quote_asset)
                case 'bitvavo':
                    commons = BitvavoCommons(exchange_connector=ccxt.bitvavo({
                        'apiKey': apis[api_or_wallet][0]['api_key'],
                        'secret': apis[api_or_wallet][0]['api_secret'],
                    }), base_asset=base_asset, quote_asset=quote_asset)
                case 'cryptocom':
                    commons = CryptocomCommons(exchange_connector=ccxt.cryptocom({
                        'apiKey': apis[api_or_wallet][0]['api_key'],
                        'secret': apis[api_or_wallet][0]['api_secret'],
                    }), base_asset=base_asset, quote_asset=quote_asset)
                case 'coinbase':
                    commons = CoinbaseCommons(exchange_connector=ccxt.coinbase({
                        'apiKey': apis[api_or_wallet][0]['api_key'],
                        'secret': apis[api_or_wallet][0]['api_secret'],
                    }), base_asset=base_asset, quote_asset=quote_asset)
                case 'lmax':
                    commons = LmaxCommons(
                        api_key=apis[api_or_wallet][0]['api_key'], 
                        api_secret=apis[api_or_wallet][0]['api_secret'], 
                        base_asset=base_asset, quote_asset=quote_asset)
                case 'coinstore':
                    commons = CoinstoreCommons(
                        api_key=apis[api_or_wallet][0]['api_key'], 
                        api_secret=apis[api_or_wallet][0]['api_secret'], 
                        base_asset=base_asset, quote_asset=quote_asset)
                case 'b2c2':
                    commons = B2C2Commons(api_token='259223adc53973b955d6b02f7facaa2b2e0397a5', base_asset=base_asset, quote_asset=quote_asset)
    
    elif exchange_or_connector in CONNECTORS:
        with open('/mnt/data/wallets.json', encoding='UTF-8') as f:
            wallets = json.load(f)   
            match exchange_or_connector:
                case 'uniswap':
                    if exchange_or_connector in wallets[api_or_wallet]['connectors']:
                        commons = GatewayCommons(chain=wallets[api_or_wallet]['chain'], network=wallets[api_or_wallet]['network'], connector=exchange_or_connector, address=wallets[api_or_wallet]['address'], base_asset=base_asset, quote_asset=quote_asset)
                case 'raydium':
                    if exchange_or_connector in wallets[api_or_wallet]['connectors']:
                        commons = RaydiumCommons(chain=wallets[api_or_wallet]['chain'], network=wallets[api_or_wallet]['network'], connector=exchange_or_connector, address=wallets[api_or_wallet]['address'], base_asset=base_asset, quote_asset=quote_asset)
                case 'jupiter':
                    if exchange_or_connector in wallets[api_or_wallet]['connectors']:
                        commons = GatewayCommons(chain=wallets[api_or_wallet]['chain'], network=wallets[api_or_wallet]['network'], connector=exchange_or_connector, address=wallets[api_or_wallet]['address'], base_asset=base_asset, quote_asset=quote_asset)
      
    return commons

