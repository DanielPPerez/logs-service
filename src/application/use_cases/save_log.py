# src/application/use_cases/save_log.py
from src.domain.models.log_entry import LogEntry
from src.application.repositories.log_repository import LogRepository
import logging

logger = logging.getLogger(__name__)

class SaveLog:
    def __init__(self, log_repository: LogRepository):
        self.log_repository = log_repository

    def execute(self, log_data: dict):
        try:
            # Validar y crear el objeto de dominio
            log_entry = LogEntry(**log_data)
            self.log_repository.save(log_entry)
            logger.info(f"Caso de uso SaveLog ejecutado para servicio: {log_entry.service}")
        except Exception as e:
            logger.error(f"Error en el caso de uso SaveLog: {e}")