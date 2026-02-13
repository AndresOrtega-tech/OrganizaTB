from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class ReminderBase(BaseModel):
    remind_at: datetime
    status: str = "pending"

class ReminderResponse(ReminderBase):
    id: str
    user_id: str
    task_id: Optional[str] = None
    event_id: Optional[str] = None
    created_at: datetime
    
    # Para mostrar detalles del origen (opcional, dependiendo de si hacemos join)
    task_title: Optional[str] = None
    event_title: Optional[str] = None

    class Config:
        orm_mode = True

class ReminderUpdate(BaseModel):
    remind_at: Optional[datetime] = None
    status: Optional[str] = None
