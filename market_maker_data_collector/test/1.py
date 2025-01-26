import binascii
import json

data = {
   "channel": "book",
   "type": "snapshot",
   "data": [
      {
         "symbol": "BTC/USD",
         "bids": [
            {
               "price": "45283.5",
               "qty": "0.10000000"
            },
            {
               "price": "45283.4",
               "qty": "1.54582015"
            },
            {
               "price": "45282.1",
               "qty": "0.10000000"
            },
            {
               "price": "45281.0",
               "qty": "0.10000000"
            },
            {
               "price": "45280.3",
               "qty": "1.54592586"
            },
            {
               "price": "45279.0",
               "qty": "0.07990000"
            },
            {
               "price": "45277.6",
               "qty": "0.03310103"
            },
            {
               "price": "45277.5",
               "qty": "0.30000000"
            },
            {
               "price": "45277.3",
               "qty": "1.54602737"
            },
            {
               "price": "45276.6",
               "qty": "0.15445238"
            }
         ],
         "asks": [
            {
               "price": "45285.2",
               "qty": "0.00100000"
            },
            {
               "price": "45286.4",
               "qty": "1.54571953"
            },
            {
               "price": "45286.6",
               "qty": "1.54571109"
            },
            {
               "price": "45289.6",
               "qty": "1.54560911"
            },
            {
               "price": "45290.2",
               "qty": "0.15890660"
            },
            {
               "price": "45291.8",
               "qty": "1.54553491"
            },
            {
               "price": "45294.7",
               "qty": "0.04454749"
            },
            {
               "price": "45296.1",
               "qty": "0.35380000"
            },
            {
               "price": "45297.5",
               "qty": "0.09945542"
            },
            {
               "price": "45299.5",
               "qty": "0.18772827"
            }
         ],
         "checksum": 3310070434
      }
   ]
}

#values = {'symbol': 'BTC/USD', 'bids': [{'price': 63275.4, 'qty': 0.03594756}, {'price': 63275.3, 'qty': 0.0001}, {'price': 63274.6, 'qty': 1.89610462}, {'price': 63274.0, 'qty': 0.0001}, {'price': 63271.5, 'qty': 0.0607641}, {'price': 63271.0, 'qty': 0.205024}, {'price': 63270.4, 'qty': 0.02125516}, {'price': 63270.3, 'qty': 0.26297963}, {'price': 63270.2, 'qty': 3.95130618}, {'price': 63270.0, 'qty': 0.06871055}, {'price': 63269.1, 'qty': 3.95137424}, {'price': 63268.3, 'qty': 0.00654347}, {'price': 63267.8, 'qty': 0.49029528}, {'price': 63267.1, 'qty': 3.95149901}, {'price': 63266.9, 'qty': 0.00015801}, {'price': 63266.3, 'qty': 0.00783585}, {'price': 63266.2, 'qty': 0.07793054}, {'price': 63266.0, 'qty': 4.75876303}, {'price': 63265.8, 'qty': 0.0002}, {'price': 63265.6, 'qty': 0.0001}, {'price': 63265.5, 'qty': 7.90318991}, {'price': 63264.1, 'qty': 0.00632364}, {'price': 63263.7, 'qty': 0.03884801}, {'price': 63263.3, 'qty': 0.00790097}, {'price': 63263.2, 'qty': 0.00790097}], 'asks': [{'price': 63275.5, 'qty': 7.90395706}, {'price': 63277.8, 'qty': 0.14935515}, {'price': 63279.6, 'qty': 0.0001}, {'price': 63279.7, 'qty': 3.95071859}, {'price': 63282.0, 'qty': 0.0371}, {'price': 63283.0, 'qty': 0.00797415}, {'price': 63284.3, 'qty': 0.0025583}, {'price': 63284.4, 'qty': 7.90084525}, {'price': 63286.4, 'qty': 0.1}, {'price': 63286.9, 'qty': 0.03149182}, {'price': 63288.6, 'qty': 0.00825082}, {'price': 63288.9, 'qty': 0.20522901}, {'price': 63293.0, 'qty': 0.01274379}, {'price': 63295.3, 'qty': 0.01555859}, {'price': 63295.4, 'qty': 0.04454749}, {'price': 63295.7, 'qty': 0.11832968}, {'price': 63295.8, 'qty': 0.03947498}, {'price': 63296.4, 'qty': 0.01509777}, {'price': 63297.1, 'qty': 0.00599912}, {'price': 63297.2, 'qty': 0.25}, {'price': 63297.5, 'qty': 0.00586656}, {'price': 63297.6, 'qty': 0.77442}, {'price': 63297.9, 'qty': 0.00260026}, {'price': 63298.0, 'qty': 7.89914797}, {'price': 63300.1, 'qty': 0.01130233}], 'checksum': 4273381060}
values = data['data'][0]
#json_data = json.loads(data)

print('data', values)

checksum_asks = ''
checksum_bids = ''

#values = data['data'][0]
for ask in values['asks']: 
    checksum_asks += str(ask['price']).replace('.', '').lstrip('0') + str(ask['qty']).replace('.', '').lstrip('0')
for bid in values['bids']: 
    checksum_bids += str(bid['price']).replace('.', '').lstrip('0') + str(bid['qty']).replace('.', '').lstrip('0')

right_checksum_asks = '45285210000045286415457195345286615457110945289615456091145290215890660452918154553491452947445474945296135380000452975994554245299518772827'
right_checksum_bids = '452835100000004528341545820154528211000000045281010000000452803154592586452790799000045277633101034527753000000045277315460273745276615445238'

#print('checksum_asks------', checksum_asks, right_checksum_asks == checksum_asks)
#print('checksum_bids------', checksum_bids, right_checksum_bids == checksum_bids)

checksum = checksum_asks + checksum_bids
right_checksum = '45285210000045286415457195345286615457110945289615456091145290215890660452918154553491452947445474945296135380000452975994554245299518772827452835100000004528341545820154528211000000045281010000000452803154592586452790799000045277633101034527753000000045277315460273745276615445238'

#print('checksum------', checksum_asks + checksum_bids, right_checksum == checksum)

print('----------', binascii.crc32(checksum.encode('utf8')), values['checksum'], values['checksum'] == binascii.crc32(checksum.encode('utf8')))
