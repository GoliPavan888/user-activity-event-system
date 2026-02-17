from pydantic import BaseModel
from typing import Dict, Any


class Event(BaseModel):
    user_id: str
    event_type: str
    timestamp: str
    metadata: Dict[str, Any]
