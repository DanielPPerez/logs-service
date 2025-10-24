# src/infrastructure/database/mongo_repository.py
import os
import pymongo
from typing import List, Optional
from src.domain.models.log_entry import LogEntry
from src.application.repositories.log_repository import LogRepository
import logging

logger = logging.getLogger(__name__)

class MongoLogRepository(LogRepository):
    def __init__(self):
        try:
            mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
            self.client = pymongo.MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
            self.client.server_info()  # Forzar conexión para validar
            self.db = self.client.log_database
            self.collection = self.db.logs
            logger.info("✅ Conexión a MongoDB exitosa.")
        except pymongo.errors.ConnectionFailure as e:
            logger.error(f"❌ No se pudo conectar a MongoDB: {e}")
            raise

    def save(self, log_entry: LogEntry) -> None:
        # Convertir el objeto Pydantic a un diccionario para guardarlo en Mongo
        log_dict = log_entry.dict(by_alias=True)
        self.collection.insert_one(log_dict)
        logger.info(f"📝 Log del servicio '{log_entry.service}' guardado en MongoDB.")

    def find(self, service: Optional[str] = None, level: Optional[str] = None, limit: int = 100) -> List[LogEntry]:
        query = {}
        if service:
            query["service"] = service
        if level:
            query["level"] = level
        
        # Buscar en la DB, ordenar por fecha (más nuevos primero) y limitar resultados
        logs_cursor = self.collection.find(query).sort("timestamp_processed", -1).limit(limit)
        
        # Convertir los documentos de Mongo a objetos Pydantic LogEntry
        return [LogEntry(**log) for log in logs_cursor]