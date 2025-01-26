import itertools
import json

exchanges = 'exchanges[ascendex,binance,bitmart,coinstore,mexc,tidex]'
exchanges = exchanges.replace('exchanges[', '').replace(']', '').split(',')
exchange_groups = list(itertools.combinations(exchanges, 2))


for exchange_group in exchange_groups:
    exchange_combinations = [
        {'exchange_1': exchange_group[0], 'exchange_2': exchange_group[1]},
        {'exchange_1': exchange_group[1], 'exchange_2': exchange_group[0]}
    ]
    print('exchange_combinations', exchange_combinations)
    
    
array_atring = ''

array = array_atring.split(',')


print('array', ' '.join([str(elem) for elem in array]))
    