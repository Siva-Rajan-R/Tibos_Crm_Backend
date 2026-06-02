from pydantic import BaseModel
from typing import Optional, Dict, Any

class CreateActivityLogDbSchema(BaseModel):
    id: str
    user_id: str
    action: str
    entity_type: str
    entity_id: str
    details: Optional[Dict[str, Any]] = None
