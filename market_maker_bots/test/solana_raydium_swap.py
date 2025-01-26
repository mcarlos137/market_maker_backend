import asyncio
import requests

async def swap_on_raydium(tokenBAddress: str, tokenAAmount: float, execute: bool) -> str:
    rsp = requests.post('http://localhost:3000/swap/send_transaction', data={
        'tokenBAddress': tokenBAddress,
        'tokenAAmount': tokenAAmount,
        'execute': execute
    })
    if rsp.status_code != 200:
        print(f'edit_bot {rsp}')
        raise Exception
    return rsp.json()

# Example usage
TOKENS: dict = {
    'SOL': 'So11111111111111111111111111111111111111112',
    'USDC': 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v'
}

amount_sol: float = 0.01
price: float = 168.35  # USDC per SOL
operation: str = 'BUY'
execute: bool = False

if operation == 'SELL':
    # SELL SOL
    tokenBAddress: str = TOKENS['USDC']
    tokenAAmount: float = amount_sol
    swap_sell_on_raydium_result: str = asyncio.run(swap_on_raydium(tokenBAddress=tokenBAddress, tokenAAmount=tokenAAmount, execute=execute))
    print("Swap SELL result:", swap_sell_on_raydium_result)

if operation == 'BUY':
    # BUY SOL
    tokenBAddress: str = TOKENS['SOL']
    tokenAAmount: float = amount_sol * price
    swap_buy_on_raydium_result: str = asyncio.run(swap_on_raydium(tokenBAddress=tokenBAddress, tokenAAmount=tokenAAmount, execute=execute))
    print("Swap BUY result:", swap_buy_on_raydium_result)