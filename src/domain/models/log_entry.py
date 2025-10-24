from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import uuid
from datetime import datetime

class LogEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    service: str
    level: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp_processed: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

    class Config:
    
        allow_population_by_field_name = True
    
        schema_extra = {
            "example": {
                "_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
                "service": "payments_service",
                "level": "ERROR",
                "message": "Falló el procesamiento del pago.",
                "details": {"order_id": "XYZ-789", "error_code": "5001"},
                "timestamp_processed": "2025-10-15T10:00:00.000Z"
            }
        }