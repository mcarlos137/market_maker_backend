import requests

API_URL = 'https://api.uat.b2c2.net/'
REST_BALANCE = '/balance'
API_TOKEN = '259223adc53973b955d6b02f7facaa2b2e0397a5'

def get_headers():
    return {'Authorization': 'Token %s' % API_TOKEN}

response = requests.get(API_URL + REST_BALANCE, headers=get_headers())
if int(response.status_code) != 200:
    raise Exception(response.reason)        
data = response.json()
balance = {}
for coin in data:
    balance[coin] = {
        'available': float(data[coin]),
        'total': float(data[coin])
    }
print('balance', balance)
