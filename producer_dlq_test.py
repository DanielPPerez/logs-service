# producer_dlq_test.py
import pika
import os
from dotenv import load_dotenv

load_dotenv() 

RABBITMQ_URI = os.getenv("RABBITMQ_URI")
EXCHANGE_NAME = 'logs_exchange'

def publish_bad_log():
    try:
        connection = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URI))
        channel = connection.channel()

        # Este mensaje NO es un JSON válido, es solo un string.
        bad_message_body = "esto no es un json"
        
        channel.basic_publish(
            exchange=EXCHANGE_NAME,
            routing_key="logs.test.critical", # Un routing key cualquiera
            body=bad_message_body,
            properties=pika.BasicProperties(delivery_mode=2)
        )
        print(f"✅ Mensaje inválido enviado para probar la DLQ.")
        connection.close()
    except Exception as e:
        print(f"❌ Error al enviar mensaje: {e}")

if __name__ == '__main__':
    publish_bad_log()