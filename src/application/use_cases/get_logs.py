# src/application/use_cases/get_logs.py
from typing import List, Optional
from src.domain.models.log_entry import LogEntry
from src.application.repositories.log_repository import LogRepository

class GetLogs:
    def __init__(self, log_repository: LogRepository):
        self.log_repository = log_repository

    def execute(self, service: Optional[str], level: Optional[str], limit: int) -> List[LogEntry]:
        return self.log_repository.find(service=service, level=level, limit=limit)