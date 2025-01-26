import pika
import sys

connection = pika.BlockingConnection(pika.ConnectionParameters('market_maker_rabbitmq'))
channel = connection.channel()

operation = sys.argv[1]
exchange = sys.argv[2]
base_asset = sys.argv[3]
quote_asset = sys.argv[4]


channel.queue_declare(queue='%s__%s__%s_%s' % (operation, exchange, base_asset, quote_asset))

#channel.basic_publish(exchange='',
#                      routing_key='hello',
#                      body='Hello World!')
#print(" [x] Sent 'Hello World!'")

connection.close()