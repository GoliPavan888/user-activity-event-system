from pydantic import BaseModel, Field
from datetime import datetime
from typing import Dict, Any


class UserActivityEvent(BaseModel):
    user_id: int = Field(..., example=123)
    event_type: str = Field(..., example="page_view")
    timestamp: datetime
    metadata: Dict[str, Any]
