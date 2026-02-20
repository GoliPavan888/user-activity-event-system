from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Dict, Any


class UserActivityEvent(BaseModel):
    user_id: int = Field(...)
    event_type: str = Field(...)
    timestamp: datetime
    metadata: Dict[str, Any]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": 123,
                "event_type": "page_view",
                "timestamp": "2023-10-27T10:00:00Z",
                "metadata": {"page_url": "/products/xyz"},
            }
        }
    )
