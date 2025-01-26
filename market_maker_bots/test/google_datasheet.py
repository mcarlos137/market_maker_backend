from datetime import datetime
import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.oauth2 import service_account

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
KEY = 'google_key.json'
# Escribe aquí el ID de tu documento:
SPREADSHEET_ID = '1W30ihejsSSLZ9MjkAvD4tWn8sAiKbOJnq_GZMwluHr8'

creds = None
creds = service_account.Credentials.from_service_account_file(KEY, scopes=SCOPES)

service = build('sheets', 'v4', credentials=creds)
sheet = service.spreadsheets()

'''
# Llamada a la api
result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range='Hoja 1!A1:A8').execute()
# Extraemos values del resultado
values = result.get('values',[])
print(values)
'''

range = 'resume!A1'

values = [['2024-05-20T22:49:22.863000', 'SELL', 0.00239, 10000.0, "{'cost': 0.0239, 'currency': 'USDT'}"], ['2024-05-20T22:49:21.618000', 'SELL', 0.002389, 9999.0, "{'cost': 0.02388761, 'currency': 'USDT'}"], ['2024-05-20T22:40:19.619000', 'SELL', 0.002383, 9999.0, "{'cost': 0.02382762, 'currency': 'USDT'}"], ['2024-05-20T22:40:14.867000', 'SELL', 0.002383, 3761.0, "{'cost': 0.00896246, 'currency': 'USDT'}"], ['2024-05-20T22:40:14.867000', 'SELL', 0.002383, 6239.0, "{'cost': 0.01486754, 'currency': 'USDT'}"], ['2024-05-20T18:58:30.058000', 'SELL', 0.002238, 2519.0, "{'cost': 0.00563752, 'currency': 'USDT'}"], ['2024-05-20T18:58:30.058000', 'SELL', 0.002238, 3431.0, "{'cost': 0.00767858, 'currency': 'USDT'}"], ['2024-05-20T18:58:25.213000', 'SELL', 0.002239, 1499.0, "{'cost': 0.00335626, 'currency': 'USDT'}"], ['2024-05-20T18:58:25.213000', 'SELL', 0.002239, 2550.0, "{'cost': 0.00570945, 'currency': 'USDT'}"], ['2024-05-20T18:58:20.627000', 'SELL', 0.002239, 10000.0, "{'cost': 0.02239, 'currency': 'USDT'}"], ['2024-05-20T18:39:31.899000', 'SELL', 0.002239, 9980.0, "{'cost': 0.02234522, 'currency': 'USDT'}"], ['2024-05-20T18:28:59.887000', 'SELL', 0.002239, 9980.0, "{'cost': 0.02234522, 'currency': 'USDT'}"], ['2024-05-20T18:28:55.825000', 'SELL', 0.002239, 1078.0, "{'cost': 0.00241364, 'currency': 'USDT'}"], ['2024-05-20T18:28:55.825000', 'SELL', 0.002239, 8922.0, "{'cost': 0.01997636, 'currency': 'USDT'}"], ['2024-05-20T18:11:31.321000', 'SELL', 0.002237, 9853.0, "{'cost': 0.02204116, 'currency': 'USDT'}"], ['2024-05-20T18:11:26.294000', 'SELL', 0.002236, 10000.0, "{'cost': 0.02236, 'currency': 'USDT'}"], ['2024-05-20T18:05:41.757000', 'SELL', 0.002232, 8828.0, "{'cost': 0.0197041, 'currency': 'USDT'}"], ['2024-05-20T18:05:36.524000', 'SELL', 0.002232, 10000.0, "{'cost': 0.02232, 'currency': 'USDT'}"], ['2024-05-20T18:05:30.965000', 'SELL', 0.002232, 10000.0, "{'cost': 0.02232, 'currency': 'USDT'}"], ['2024-05-20T18:05:24.803000', 'SELL', 0.002232, 10000.0, "{'cost': 0.02232, 'currency': 'USDT'}"], ['2024-05-20T17:57:56.511000', 'SELL', 0.002233, 8947.0, "{'cost': 0.01997865, 'currency': 'USDT'}"], ['2024-05-20T17:57:50.803000', 'SELL', 0.002233, 10000.0, "{'cost': 0.02233, 'currency': 'USDT'}"], ['2024-05-20T17:57:45.430000', 'SELL', 0.002233, 10000.0, "{'cost': 0.02233, 'currency': 'USDT'}"], ['2024-05-20T17:57:40.187000', 'SELL', 0.002233, 10000.0, "{'cost': 0.02233, 'currency': 'USDT'}"], ['2024-05-20T17:41:17.092000', 'SELL', 0.002222, 3216.0, "{'cost': 0.00714595, 'currency': 'USDT'}"], ['2024-05-20T17:41:17.092000', 'SELL', 0.002222, 6784.0, "{'cost': 0.01507405, 'currency': 'USDT'}"], ['2024-05-20T17:34:58.335000', 'SELL', 0.002226, 8477.0, "{'cost': 0.0188698, 'currency': 'USDT'}"], ['2024-05-20T17:34:52.976000', 'SELL', 0.002226, 10000.0, "{'cost': 0.02226, 'currency': 'USDT'}"], ['2024-05-20T17:34:47.469000', 'SELL', 0.002226, 10000.0, "{'cost': 0.02226, 'currency': 'USDT'}"], ['2024-05-20T17:34:42.158000', 'SELL', 0.002226, 10000.0, "{'cost': 0.02226, 'currency': 'USDT'}"], ['2024-05-20T01:28:31.692000', 'SELL', 0.002142, 10000.0, "{'cost': 0.02142, 'currency': 'USDT'}"], ['2024-05-20T01:28:27.606000', 'SELL', 0.002141, 4863.0, "{'cost': 0.01041168, 'currency': 'USDT'}"], ['2024-05-20T01:28:27.606000', 'SELL', 0.002141, 5137.0, "{'cost': 0.01099832, 'currency': 'USDT'}"]]

#values = [['2024-05-20T22:49:22.863000', 'SELL', 0.00239, 10000.0, "{'cost': 0.0239, 'currency': 'USDT'}"]]
          

#Type	Date	Avg. price	Fee (binance)	HOT	USDT	After exchange Fee


if len(values) <= 0:
    raise

base_asset = 'HOT'
quote_asset = 'USDT'

new_values = []
dates = []

type = f'SELL {base_asset} to {quote_asset}'
date = None
avg_price = 0
fee = 0
base_amount = 0
quote_amount = 0
after_exchange_fee = 0

for value in values:
    new_date = str(value[0]).split('T')[0]
    value[4] = str(value[4]).replace("'", '"')
    new_fee = json.loads(value[4])
    if date is None or new_date != date:
        date = new_date
        dates.append(date)
        new_values.append([type, date, avg_price, fee, base_amount, quote_amount, after_exchange_fee])
    new_value = [new_value for new_value in new_values if new_value[1] == date][0]
    new_value[3] += new_fee['cost']
    new_value[4] += value[3]
    new_value[5] += value[2] * value[3] 
    new_value[6] += (value[2] * value[3]) - new_fee['cost']
    [new_value for new_value in new_values if new_value[1] == date][0] = new_value    
    
for date in dates:
	[new_value for new_value in new_values if new_value[1] == date][0][2] = [new_value for new_value in new_values if new_value[1] == date][0][5] / [new_value for new_value in new_values if new_value[1] == date][0][4]


# Llamamos a la api
result = sheet.values().append(spreadsheetId=SPREADSHEET_ID,
							range=range,
							valueInputOption='USER_ENTERED',
							body={'values':new_values}).execute()
print(f"Datos insertados correctamente.\n{(result.get('updates').get('updatedCells'))}")