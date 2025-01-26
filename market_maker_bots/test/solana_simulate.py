from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solana.rpc.api import Client
from solders.system_program import TransferParams, transfer
from solana.transaction import Transaction
from solders.rpc.responses import SimulateTransactionResp

private_key =
sender = Keypair.from_base58_string('private_key_solana')
print('sender', sender.pubkey())
#receiver = Keypair().pubkey()
receiver = Pubkey.from_string('2c72iP4rfHwBUnTxVZ9J35tnvEDnMJ3nymaTCNburuCk')
print('receiver', receiver)
transfer_ix = transfer(TransferParams(from_pubkey=sender.pubkey(), to_pubkey=receiver, lamports=1_000_000))
txn = Transaction().add(transfer_ix)
print('txn', txn)
solana_client = Client("https://api.mainnet-beta.solana.com") # replace with a real RPC
simulate_transaction_response: SimulateTransactionResp = solana_client.simulate_transaction(txn=txn)
print('simulate_transaction_response', simulate_transaction_response)