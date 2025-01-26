from solana.rpc.api import Client
from solders.pubkey import Pubkey


RPC_URL = 'https://api.mainnet-beta.solana.com'
ADDRESS = '5SFRdzQxvKYwBo8Ex7HMzJaSfDDmLoyeKX6HjhNbsSFm'
api_client = Client(RPC_URL)

pub_key = Pubkey.from_string(ADDRESS)
#account_info = api_client.get_account_info_json_parsed(pubkey=pub_key)
account_info = api_client.get_account_info(pubkey=pub_key)

print('account_info', account_info)
