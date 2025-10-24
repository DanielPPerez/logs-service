import pika
import json
import os
from dotenv import load_dotenv

# --- CAMBIO IMPORTANTE AQUÍ ---
# Cargar las variables de entorno desde el archivo específico para pruebas locales
load_dotenv(dotenv_path='.env')

RABBITMQ_URI = os.getenv("RABBITMQ_URI")
EXCHANGE_NAME = 'logs_exchange'

def publish_log(routing_key, message: dict):
    try:
        # El resto del código no necesita cambios
        connection = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URI)) # type: ignore
        channel = connection.channel()

        channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type='topic', durable=True)

        channel.basic_publish(
            exchange=EXCHANGE_NAME,
            routing_key=routing_key,
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=2,
            ))
        print(f"✅ Log enviado con routing key '{routing_key}': {message}")
        connection.close()
    except pika.exceptions.AMQPConnectionError as e:
        print(f"❌ No se pudo conectar a RabbitMQ: {e}")
    except Exception as e:
        print(f"❌ Ocurrió un error inesperado al publicar: {e}")

if __name__ == '__main__':
    # Simular un log de éxito del servicio de Usuarios
    log_user_success = {
        "service": "users_service",
        "level": "INFO",
        "message": "Usuario 'john.doe' creado exitosamente.",
        "details": {"user_id": 123, "email": "john.doe@example.com"}
    }
    publish_log('logs.users.info', log_user_success)

    # Simular un log de error del servicio de Pagos
    log_payment_error = {
        "service": "payments_service",
        "level": "ERROR",
        "message": "Falló el procesamiento del pago.",
        "details": {"order_id": "XYZ-789", "error_code": "5001", "reason": "Fondos insuficientes"}
    }
    publish_log('logs.payments.error', log_payment_error)