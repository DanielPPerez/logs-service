import json
import pika
import os
import time
from dotenv import load_dotenv
from src.application.use_cases.save_log import SaveLog
import logging

# Cargar variables de entorno del archivo .env
load_dotenv()

# Obtener una instancia del logger. La configuración básica se hace en api.py
logger = logging.getLogger(__name__)

class RabbitMQConsumer:
    """
    Gestiona la conexión con RabbitMQ y el consumo de mensajes de log.
    Implementa lógica de reconexión y Dead-Letter Queue (DLQ).
    """
    def __init__(self, save_log_use_case: SaveLog):
        """
        Inicializa el consumidor.
        Args:
            save_log_use_case (SaveLog): El caso de uso para guardar logs,
                                         inyectado para mantener la separación de capas.
        """
        self.save_log_use_case = save_log_use_case
        
        # --- Configuración Principal de RabbitMQ ---
        self.RABBITMQ_URI = os.getenv("RABBITMQ_URI", "amqp://guest:guest@localhost/")
        self.EXCHANGE_NAME = 'logs_exchange'
        self.QUEUE_NAME = 'logs_queue'
        self.ROUTING_KEY = 'logs.*.*'

        # --- Configuración de la Dead-Letter Queue (DLQ) ---
        self.DLX_EXCHANGE_NAME = 'logs_exchange_dlx'
        self.DLQ_NAME = 'logs_queue_dlx'
        self.DLQ_ROUTING_KEY = 'dlq.logs'

    def _process_log_callback(self, ch, method, properties, body):
        """
        Callback que se ejecuta con cada mensaje recibido.
        Decodifica el mensaje, lo pasa al caso de uso y maneja errores.
        """
        try:
            log_data = json.loads(body)
            logger.info(f"▶️ Log recibido (Routing Key: {method.routing_key})")
            
            # Delega el procesamiento al caso de uso de la capa de aplicación
            self.save_log_use_case.execute(log_data)
            
            # Confirma que el mensaje ha sido procesado exitosamente
            ch.basic_ack(delivery_tag=method.delivery_tag)
            
        except json.JSONDecodeError:
            logger.error(f"❌ Mensaje no es un JSON válido. Enviando a DLQ. Mensaje: {body}")
            # Rechaza el mensaje y no lo vuelve a encolar, activando la DLQ
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            
        except Exception as e:
            logger.error(f"❌ Error inesperado al procesar log. Enviando a DLQ. Error: {e}")
            # Rechaza el mensaje y no lo vuelve a encolar, activando la DLQ
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        
    def start(self):
        """
        Inicia el bucle principal del consumidor con reconexión automática.
        """
        while True:
            try:
                logger.info("▶️ Intentando conectar a RabbitMQ...")
                connection = pika.BlockingConnection(pika.URLParameters(self.RABBITMQ_URI))
                channel = connection.channel()

                # --- Declaración de la infraestructura de la DLQ (es idempotente) ---
                # 1. Declarar el exchange para los mensajes muertos (DLX)
                channel.exchange_declare(exchange=self.DLX_EXCHANGE_NAME, exchange_type='topic', durable=True)
                # 2. Declarar la cola de mensajes muertos (DLQ)
                channel.queue_declare(queue=self.DLQ_NAME, durable=True)
                # 3. Vincular la DLQ al DLX
                channel.queue_bind(exchange=self.DLX_EXCHANGE_NAME, queue=self.DLQ_NAME, routing_key=f"{self.DLQ_ROUTING_KEY}.#")

                # --- Declaración de la infraestructura principal ---
                # 1. Declarar el exchange principal
                channel.exchange_declare(exchange=self.EXCHANGE_NAME, exchange_type='topic', durable=True)
                
                # 2. Argumentos para vincular la cola principal a la DLX
                queue_args = {
                    "x-dead-letter-exchange": self.DLX_EXCHANGE_NAME,
                    "x-dead-letter-routing-key": self.DLQ_ROUTING_KEY
                }
                # 3. Declarar la cola principal
                channel.queue_declare(queue=self.QUEUE_NAME, durable=True, arguments=queue_args)

                # 4. Vincular la cola principal al exchange principal
                channel.queue_bind(exchange=self.EXCHANGE_NAME, queue=self.QUEUE_NAME, routing_key=self.ROUTING_KEY)

                logger.info("✅ Conexión a RabbitMQ exitosa. Esperando logs...")
                
                # Configurar el consumidor para que use nuestro callback
                channel.basic_consume(queue=self.QUEUE_NAME, on_message_callback=self._process_log_callback)
                
                # Iniciar el consumo de mensajes (bucle bloqueante)
                channel.start_consuming()

            except (pika.exceptions.AMQPConnectionError, pika.exceptions.StreamLostError) as e:
                logger.error(f"❌ Conexión con RabbitMQ perdida o no establecida: {e}. Reintentando en 5 segundos...")
                time.sleep(5)
            except Exception as e:
                logger.critical(f"❌ Ocurrió un error fatal en el consumidor: {e}", exc_info=True)
                time.sleep(10)