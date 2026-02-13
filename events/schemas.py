from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from tasks.schemas import ReminderConfig, ReminderResponse
try:
    from backend.tags.schemas import TagResponse
except ImportError:
    from tags.schemas import TagResponse

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

class EventLinkTask(BaseModel):
    event_id: str
    task_id: str

class EventLinkNote(BaseModel):
    event_id: str
    note_id: str

class EventAssignTags(BaseModel):
    event_id: str = Field(..., description="ID del evento a etiquetar")
    tag_ids: List[str] = Field(..., description="Lista de IDs de las etiquetas a asignar")

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
    tags: List[TagResponse] = []
    tasks: List[TaskSummary] = []
    notes: List[NoteSummary] = []
    has_reminder: bool = False
    
    class Config:
        from_attributes = True
