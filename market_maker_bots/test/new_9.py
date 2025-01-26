pair = 'DAMEX-USDT'
exchange = 'tidex'
order_books = {
    pair: {
        exchange: {
            'asks': [],
            'bids': [],
        },
        'coinstore': {
            'asks': [],
            'bids': [],
        }
    }
}

print('order_books 1', order_books)

del order_books[pair][exchange]

print('order_books 2', order_books)