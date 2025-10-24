# src/application/repositories/log_repository.py
from abc import ABC, abstractmethod
from typing import List, Optional
from src.domain.models.log_entry import LogEntry

class LogRepository(ABC):
    """
    Interfaz abstracta para el repositorio de logs.
    Define los métodos que cualquier implementación de repositorio debe tener.
    """
    @abstractmethod
    def save(self, log_entry: LogEntry) -> None:
        pass

    @abstractmethod
    def find(self, service: Optional[str] = None, level: Optional[str] = None, limit: int = 100) -> List[LogEntry]:
        pass