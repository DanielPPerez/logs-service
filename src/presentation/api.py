# src/presentation/api.py
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from typing import List, Optional
from contextlib import asynccontextmanager
import threading
import logging

# Importaciones de nuestra arquitectura
from src.domain.models.log_entry import LogEntry
from src.application.use_cases.get_logs import GetLogs
from src.application.use_cases.save_log import SaveLog
from src.infrastructure.database.mongo_repository import MongoLogRepository
from src.infrastructure.messaging.rabbitmq_consumer import RabbitMQConsumer

# --- Configuración de Logging ---
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] - [%(levelname)s] - %(message)s')
logger = logging.getLogger(__name__)

# --- Inyección de Dependencias (instanciación de nuestras clases) ---
log_repository = MongoLogRepository()
get_logs_use_case = GetLogs(log_repository)
save_log_use_case = SaveLog(log_repository)
rabbitmq_consumer = RabbitMQConsumer(save_log_use_case)

# --- Lógica de Startup/Shutdown de FastAPI ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Iniciando servicio...")
    # Iniciar el consumidor en un hilo separado
    consumer_thread = threading.Thread(target=rabbitmq_consumer.start, daemon=True)
    consumer_thread.start()
    yield
    logger.info("🛑 Apagando servicio.")

app = FastAPI(
    title="Servicio de Logs",
    description="API para centralizar y consultar logs de microservicios.",
    version="1.0.0",
    lifespan=lifespan
)

# Middleware de seguridad (MSTG-NETWORK-1)
# Solo acepta requests del API Gateway o hosts confiables
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["api.scriptoria.com", "localhost", "logs-service", "127.0.0.1"]
)

# --- Endpoints de la API ---
@app.get(
    "/logs",
    response_model=List[LogEntry],
    summary="Consultar logs con filtros",
    tags=["Logs"]
)
def get_logs(
    service: Optional[str] = Query(None, description="Filtrar por nombre del servicio. Ej: 'payments_service'"),
    level: Optional[str] = Query(None, description="Filtrar por nivel de log. Ej: 'ERROR'"),
    limit: int = Query(100, ge=1, le=1000, description="Número de logs a devolver")
):
    """
    Obtiene una lista de logs, permitiendo filtrar por servicio y nivel.
    - Los logs se devuelven ordenados del más reciente al más antiguo.
    """
    try:
        logs = get_logs_use_case.execute(service=service, level=level, limit=limit)
        return logs
    except Exception as e:
        logger.error(f"Error al obtener logs: {e}")
        raise HTTPException(status_code=500, detail="Ocurrió un error interno al consultar los logs.")

@app.get("/", tags=["Health Check"])
def health_check():
    return {"status": "Servicio de Logs está activo y saludable"}