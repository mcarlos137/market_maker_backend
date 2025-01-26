#USABLE

import json
from solana.rpc.api import Client
from spl.token.client import Token
from solders.pubkey import Pubkey
from solders.keypair import Keypair

#mint = Pubkey.from_string('Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB') #eg: https://solscan.io/token/FpekncBMe3Vsi1LMkh6zbNq8pdM6xEbNiFsJBRcPbMDQ**
mint = Pubkey.from_string('H3cb6GkPPnT7USCebarN8KtHRTa6Ea3ynF3XfUMeVnVh') #eg: https://solscan.io/token/FpekncBMe3Vsi1LMkh6zbNq8pdM6xEbNiFsJBRcPbMDQ**
program_id = Pubkey.from_string('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA') #eg: https://solscan.io/account/**TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA**

wallet_solana = json.loads(open('../base/wallet_solana_test.json', 'r').read())
print('wallet_solana', wallet_solana)

key_pair = Keypair.from_base58_string(wallet_solana['private_key'])
solana_client = Client("https://api.mainnet-beta.solana.com")
spl_client = Token(conn=solana_client, pubkey=mint, program_id=program_id, payer=key_pair)

source = key_pair.pubkey()
dest = Pubkey.from_string('2c72iP4rfHwBUnTxVZ9J35tnvEDnMJ3nymaTCNburuCk')

print('spl_client', spl_client)

try:
    source_token_account = spl_client.get_accounts_by_owner(owner=source, commitment=None, encoding='base64').value[0].pubkey
except:
    source_token_account = spl_client.create_associated_token_account(owner=source, skip_confirmation=False, recent_blockhash=None)
try:
    dest_token_account = spl_client.get_accounts_by_owner(owner=dest, commitment=None, encoding='base64').value[0].pubkey
except:
    dest_token_account = spl_client.create_associated_token_account(owner=dest, skip_confirmation=False, recent_blockhash=None)

print('source_token_account', source_token_account)
print('dest_token_account', dest_token_account)

raise
amount = 1.0

transaction = spl_client.transfer(source=source_token_account, dest=dest_token_account, owner=key_pair, amount=int(float(amount)*1000000000), multi_signers=None, opts=None, recent_blockhash=None)
print('transaction', transaction)