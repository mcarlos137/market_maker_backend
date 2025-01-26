import requests
 
strategy = 'maker_binance_holo_v2' 
 
payload = {
    'username': "carlos",
    'bot_id': "101",
    'bot_type': "maker",
    'new_attributes_values': "{\"strategy\": \"" + strategy + "\"}"
}

session = requests.Session()
response = session.post('https://restmm.damex.io/exchange/edit_bot', data=payload) 
 
#response = requests.post('https://restmm.damex.io/exchange/edit_bot', headers=headers, data=data)   
  
        
print('response----------', response.headers)
if response.status_code != 200:
    print(f'edit_bot {response.status_code} {response.reason}')        
    
print('response----------', response.json())
        