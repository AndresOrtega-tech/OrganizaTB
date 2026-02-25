from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from tasks.schemas import ReminderConfig, ReminderResponse
try:
    from backend.tags.schemas import TagSummary
except ImportError:
    from tags.schemas import TagSummary

class EventBase(BaseModel):
    title: str = Field(..., min_length=1, description="Título del evento")
    description: Optional[str] = Field(None, description="Descripción del evento", max_length=500)
    start_time: datetime = Field(..., description="Fecha y hora de inicio del evento")
    end_time: datetime = Field(..., description="Fecha y hora de fin del evento")
    location: Optional[str] = Field(None, description="Ubicación del evento")
    is_all_day: bool = Field(False, description="Indica si es evento de todo el día")

class EventCreate(EventBase):
    reminders: Optional[List[ReminderConfig]] = Field(None, description="Configuración de recordatorios")

class EventUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1)
    description: Optional[str] = Field(None, max_length=500)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    location: Optional[str] = None
    is_all_day: Optional[bool] = None
    reminders: Optional[List[ReminderConfig]] = Field(None, description="Nueva lista de recordatorios")

class EventAssignTag(BaseModel):
    tag_id: str = Field(..., description="ID de la etiqueta a asignar al evento")

class TaskSummary(BaseModel):
    id: str
    title: str
    is_completed: bool

class NoteSummary(BaseModel):
    id: str
    title: Optional[str] = None

class EventResponse(EventBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    reminders_data: List[ReminderResponse] = []
    has_reminder: bool = False
    tags: List[TagSummary] = Field(default=[], description="Etiquetas vinculadas al evento")
    
    class Config:
        from_attributes = True

class EventRelatedResponse(BaseModel):
    tags: List[TagSummary] = []
    tasks: List[TaskSummary] = []
    notes: List[NoteSummary] = []
