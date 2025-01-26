import asyncio
import json
from solana.rpc.async_api import AsyncClient
from solana.rpc.types import TokenAccountOpts
from solders.rpc.responses import GetBalanceResp, GetTokenAccountsByOwnerJsonParsedResp
from solders.pubkey import Pubkey
from solders.keypair import Keypair

TOKENS = {
    'Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB': 'USDT',
    'H3cb6GkPPnT7USCebarN8KtHRTa6Ea3ynF3XfUMeVnVh': 'DAMEX'
}

async def main():
    async with AsyncClient("https://api.mainnet-beta.solana.com") as client:
        #res = await client.is_connected()
        #pub_key = Pubkey([0] * 31 + [1])
        pub_key = Pubkey.from_string('5SFRdzQxvKYwBo8Ex7HMzJaSfDDmLoyeKX6HjhNbsSFm')
        pub_key_token = Pubkey.from_string('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA')
        #pub_key = Pubkey.new_unique()
        #key_pair = Keypair.from_base58_string('private_key_solana')
        #pub_key = key_pair.pubkey()
        print('pub_key', pub_key)
        get_balance_response: GetBalanceResp = await client.get_balance(pub_key)
        get_balance = json.loads(get_balance_response.to_json())
        get_token_accounts_by_owner_json_parsed_response: GetTokenAccountsByOwnerJsonParsedResp = await client.get_token_accounts_by_owner_json_parsed(owner=pub_key, opts=TokenAccountOpts(program_id=pub_key_token))
        get_token_accounts_by_owner_json_parsed = json.loads(get_token_accounts_by_owner_json_parsed_response.to_json())
        #res = await client.get_account_info(pub_key)
        #res = await client.get_token_accounts_by_owner_json_parsed(owner=pub_key, opts=TokenAccountOpts(program_id=pub_key_token))
    
    #for r in res:
    #    print('r', r)
    #print('get_balance', get_balance['result']['value'])  # True
    #print('get_token_accounts_by_owner_json_parsed', get_token_accounts_by_owner_json_parsed['result']['value'])
    
    balance = {
        'SOL': float(get_balance['result']['value']) / 1e9,
    }
    for value in get_token_accounts_by_owner_json_parsed['result']['value']:
        token = value['account']['data']['parsed']['info']
        balance[TOKENS[token['mint']]] = float(token['tokenAmount']['uiAmount'])
    
    print('balance', balance)

    # Alternatively, close the client explicitly instead of using a context manager:
    '''
    client = AsyncClient("https://api.devnet.solana.com")
    res = await client.is_connected()
    print(res)  # True
    await client.close()
    '''
    
asyncio.run(main())