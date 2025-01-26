#USABLE

import json
import requests
import json
from solana.rpc.api import Client
from solders.message import Message # type: ignore
from solders.transaction import Transaction # type: ignore
from solders.system_program import transfer, TransferParams
from solders.pubkey import Pubkey as PublicKey # type: ignore
from solders.keypair import Keypair # type: ignore
from solders.hash import Hash # type: ignore
from solders.commitment_config import CommitmentLevel # type: ignore
from solders.rpc.config import RpcSendTransactionConfig # type: ignore
from solders.rpc.requests import SendLegacyTransaction # type: ignore
from solders.rpc.responses import GetLatestBlockhashResp # type: ignore

SOL_TO_LAMPORTS = 10000000

wallet_solana = json.loads(open('../base/wallet_solana_test.json', 'r').read())
print('wallet_solana', wallet_solana)

from_keypair = Keypair.from_base58_string(wallet_solana['private_key'])
to = PublicKey.from_string("2c72iP4rfHwBUnTxVZ9J35tnvEDnMJ3nymaTCNburuCk")
instruction = transfer(
    TransferParams(
        from_pubkey = from_keypair.pubkey(),
        to_pubkey = to,
        lamports = SOL_TO_LAMPORTS
    )
)
print('instruction', instruction)

# solana api to get recent blockhash
solana_client = Client('https://api.mainnet-beta.solana.com', timeout=30)
get_latest_blockhash_resp: GetLatestBlockhashResp = solana_client.get_latest_blockhash()
print('get_latest_blockhash_resp', get_latest_blockhash_resp)
get_latest_blockhash = json.loads(get_latest_blockhash_resp.to_json())
print('get_latest_blockhash', get_latest_blockhash)
blockhash = Hash.from_string(get_latest_blockhash['result']['value']['blockhash'])
print('blockhash', blockhash)


message = Message([instruction], from_keypair.pubkey())
tx = Transaction([from_keypair], message, blockhash)

print('message', message)
print('tx', tx)

commitment = CommitmentLevel.Confirmed
config = RpcSendTransactionConfig(preflight_commitment=commitment)
req = SendLegacyTransaction(tx, config)
as_json = req.to_json()  # as_json returns a string not a json

print('as_json', as_json)

print('sending', SOL_TO_LAMPORTS, 'to', to)

res = requests.post('https://api.mainnet-beta.solana.com', json=json.loads(as_json))
print('---------------->', res.json())