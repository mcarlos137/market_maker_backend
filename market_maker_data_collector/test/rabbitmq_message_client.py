import pika
import json
import sys

operation = sys.argv[1]
exchange = sys.argv[2]
base_asset = sys.argv[3]
quote_asset = sys.argv[4]

def callback(ch, method, properties, body):
    print(f"Received", operation, exchange, base_asset, quote_asset, json.loads(body))

connection = pika.BlockingConnection(pika.ConnectionParameters('market_maker_rabbitmq'))
channel = connection.channel()

channel.basic_consume(queue='%s__%s__%s_%s' % (operation, exchange, base_asset, quote_asset),
                      auto_ack=True,
                      on_message_callback=callback)

channel.start_consuming()

