'''
order_book_1 = {
    'asks': [
        [0.250, 100],
        [0.251, 150],
        [0.252, 100],
        [0.253, 80],
        [0.254, 100],
    ]
}

order_book_2 = {
    'bids': [
        [0.261, 300],
        [0.260, 120],
        [0.259, 130],
        [0.253, 80],
        [0.250, 100],
    ]
}
'''
order_book_1 = {
    'asks': [
        [0.250, 100],
        [0.251, 150],
        [0.252, 100],
        [0.253, 80],
        [0.254, 100],
    ]
}

order_book_2 = {
    'bids': [
        [0.259, 300],
        [0.258, 120],
        [0.257, 130],
        [0.256, 80],
        [0.255, 100],
    ]
}

min_spread_percent = 2

print('----------------------------------')
total_bid_amount = 0
bids_price_per_amount_sum = 0
first_ask_price = order_book_1['asks'][0][0]
for bid in order_book_2['bids']:
    bid_price = bid[0]
    bid_amount = bid[1]
    if first_ask_price * (1 + (min_spread_percent / 100)) < bid_price:
        bids_price_per_amount_sum += bid_price * bid_amount
        total_bid_amount += bid_amount
total_ask_amount = 0
asks_price_per_amount_sum = 0
first_bid_price = order_book_2['bids'][0][0]
for ask in order_book_1['asks']:
    ask_price = ask[0]
    ask_amount = ask[1]
    if first_bid_price > ask_price * (1 + (min_spread_percent / 100)):
        asks_price_per_amount_sum += ask_price * ask_amount
        total_ask_amount += ask_amount
depth = total_bid_amount
if total_ask_amount < depth:
    depth = total_ask_amount
if depth > 0:
    ask_avg_price = asks_price_per_amount_sum / total_ask_amount
    bid_avg_price = bids_price_per_amount_sum / total_bid_amount

print('----------------------------------')
