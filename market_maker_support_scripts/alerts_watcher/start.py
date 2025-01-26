import time
import json
import logging
import requests
import asyncio
import pytz
from logging.handlers import RotatingFileHandler
from datetime import datetime
from watchdog.observers.polling import PollingObserver
from watchdog.events import FileSystemEventHandler
from damexCommons.tools.utils import BASE_PATH


DIRECTORIES_TO_WATCH = [BASE_PATH + "/alert_files"]
MESSAGES = {
    'bot_activate': 'Bot $TYPE $ID $REGION strategy $STRATEGY was activated',
    'bot_inactivate': 'Bot $TYPE $ID $REGION strategy $STRATEGY was inactivated',
    'bot_restart': 'Bot $TYPE $ID $REGION strategy $STRATEGY was restarted',
    'or_action': 'Orchestration Rule $ID $REGION strategy $STRATEGY was $ACTION',
    'or_target_failed': 'Orchestration Rule $ID $REGION failed at creating target for $EXCHANGE $BASE_ASSET-$QUOTE_ASSET to $OPERATION',
    'trades_sell_report_default': '$EXCHANGE has $QUANTITY sell trades today at $PRICE_AVERAGE. Total sold amount is $BASE_AMOUNT $BASE_ASSET collecting $QUOTE_AMOUNT $QUOTE_ASSET',
    'trades_sell_report_strategy': '$EXCHANGE has: $MESSAGE',
    'trades_sell_report_client1': '$DATE %0A$BASE_AMOUNT $BASE_ASSET sold for $QUOTE_AMOUNT $QUOTE_ASSET %0AAvg Price $PRICE_AVERAGE',
    'balance': '$EXCHANGE has $BASE_AMOUNT $BASE_ASSET and $QUOTE_AMOUNT $QUOTE_ASSET',
    'or_status': 'Orchestration rule $TARGET_ID to $OPERATION $OP_AMOUNT $ASSET IS $STATUS',
    'arbitrage_candidate': 'Market: $BASE_ASSET-$QUOTE_ASSET %0ADepth: $DEPTH $BASE_ASSET %0ALevels: $LEVELS %0ABuy at: $EXCHANGE_1 $PRICE_BUY_1 $QUOTE_ASSET/$BASE_ASSET %0ASell at: $EXCHANGE_2 $PRICE_SELL_2 $QUOTE_ASSET/$BASE_ASSET %0AArb opportunity: $ARB_OPPORTUNITY $QUOTE_ASSET/$BASE_ASSET %0AProfitability: $PROFITABILITY%25 %0APotential profit: $PROFIT $QUOTE_ASSET',
}

TELEGRAM_GROUP_IDS = {
    'telegram_group_1': '-1002034464468',
    # client 'telegram_group_2': '-441646973',
    'telegram_group_2': '-4276564732',
    'telegram_group_3': '-4279082250',   
}

TELEGRAM_AUTH_TOKENS = {
    'telegram_group_1': '7073034938:AAG0cau9pl8rX-RpQh5Nu5tP-inmxoH1pD0',
    'telegram_group_2': '7073034938:AAG0cau9pl8rX-RpQh5Nu5tP-inmxoH1pD0',
    'telegram_group_3': '7389476607:AAF-XzSO89UPW9uZuXSCen8Jnes6SmrC4WU',
}

def parse_message(message: str, message_values: dict):
    current_datetime = datetime.now(pytz.timezone('UTC'))
    message_values['date'] = current_datetime.strftime("%d-%m-%Y")
    message_values['time'] = current_datetime.strftime("%H:%M:%S")
    for message_value in message_values:
        key = '$' + str(message_value).upper()
        message = message.replace(key, str(message_values[message_value]))
    
    return message

def send_message_on_telegram(message, telegram_group_id, telegram_auth_token):
    telegram_api_url = f"https://api.telegram.org/bot{telegram_auth_token}/sendMessage?chat_id={telegram_group_id}&text={message}"
    print('telegram_api_url', telegram_api_url)
    try:
        telelegram_resp = requests.get(telegram_api_url, timeout=7)
        telelegram_resp.raise_for_status()
        print ("Notification has been sent on Telegram") 
    except requests.exceptions.HTTPError as e:
        print ("Could not send Message", e.response.text)        

class Watcher:
    
    def __init__(self):
        self.observer = PollingObserver()
        self.operation = 'alerts_watcher'
        
        logging.basicConfig(
            level=logging.INFO, 
            handlers=[
                RotatingFileHandler(f"{self.operation}.log", mode='a', maxBytes=1024*1024*10, backupCount=10, encoding=None, delay=0),
                logging.StreamHandler()
            ],
            format="%(asctime)s %(levelname)s %(message)s"
        )

    def run(self):
        logging.info('ADDING WATCHERS')
        threads = []
        for i in range(len(DIRECTORIES_TO_WATCH)):
            event_handler = Handler()
            self.observer.schedule(event_handler, DIRECTORIES_TO_WATCH[i], recursive=False)
            threads.append(self.observer)
        self.observer.start()
        try:
            while True:
                time.sleep(0.1)
        except KeyboardInterrupt:
            self.observer.stop()
        self.observer.join()


class Handler(FileSystemEventHandler):

    @staticmethod
    def on_any_event(event):
        if event.is_directory:
            return None

        elif event.event_type == 'created':
            # Take any action here when a file is first created.
            logging.info("Received created event - %s.", event.src_path)
            if "alert_files" in event.src_path: 
                try:
                    alert = json.loads(open(event.src_path, 'r', encoding='UTF-8').read())
                except UnicodeDecodeError as error:
                    logging.error('error %s', error)
                    return
                if 'type' not in alert or 'message_values' not in alert or 'channel' not in alert:
                    logging.info('params are missing in the request %s', alert)
                    return
                if alert['type'] not in MESSAGES:
                    logging.info('message type does not exist %s', alert)
                    return
                message = parse_message(message=MESSAGES[alert['type']], message_values=alert['message_values'])
                if alert['channel'] not in TELEGRAM_GROUP_IDS:
                    logging.info('telegram group id not found %s', alert['channel'])
                    return
                logging.info('message %s', message)
                send_message_on_telegram(message=message, telegram_group_id=TELEGRAM_GROUP_IDS[alert['channel']], telegram_auth_token=TELEGRAM_AUTH_TOKENS[alert['channel']])             
                                                                            
        elif event.event_type == 'modified':
            # Taken any action here when a file is modified.
            logging.info("Received modified event - %s.", event.src_path)


async def listen():
    watcher = Watcher()
    watcher.run()
    logging.info('WATCHER INITIATED')
    while True:
        continue

asyncio.get_event_loop().run_until_complete(listen())