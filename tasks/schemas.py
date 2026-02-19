from pydantic import BaseModel, Field, validator
from typing import Optional, List, Literal
from datetime import datetime

try:
    from backend.tags.schemas import TagResponse
except ImportError:
    from tags.schemas import TagResponse

class ReminderConfig(BaseModel):
    value: int = Field(..., gt=0, description="Cantidad de tiempo antes del vencimiento")
    unit: Literal["minutes", "hours", "days"] = Field(..., description="Unidad de tiempo (minutes, hours, days)")

class ReminderResponse(BaseModel):
    id: str
    remind_at: datetime
    status: str

class NoteSummary(BaseModel):
    id: str
    title: Optional[str] = None
    content: Optional[str] = None

class EventSummary(BaseModel):
    id: str
    title: str
    start_time: datetime

class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, description="Título de la tarea")
    description: Optional[str] = Field(None, description="Descripción detallada de la tarea", max_length=500)
    due_date: Optional[datetime] = Field(None, description="Fecha límite de la tarea")
    is_completed: bool = Field(False, description="Estado de completado de la tarea")
    priority: Literal["baja", "media", "alta"] = Field("media", description="Prioridad de la tarea")

class TaskCreate(TaskBase):
    reminders: Optional[List[ReminderConfig]] = Field(None, description="Configuración de recordatorios (tiempo antes del vencimiento)")
    # calendar_event_id se generará automáticamente igual al ID de la tarea
    # media_url es null por ahora

class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1)
    description: Optional[str] = Field(None, max_length=500)
    due_date: Optional[datetime] = None
    is_completed: Optional[bool] = None
    priority: Optional[Literal["baja", "media", "alta"]] = None
    reminders: Optional[List[ReminderConfig]] = Field(None, description="Nueva lista de recordatorios (reemplaza los existentes)")

class TaskAssignTags(BaseModel):
    task_id: str = Field(..., description="ID de la tarea a la que se asignarán las etiquetas")
    tag_ids: List[str] = Field(..., description="Lista de IDs de las etiquetas a asignar")

class TaskLinkNote(BaseModel):
    task_id: str = Field(..., description="ID de la tarea")
    note_id: str = Field(..., description="ID de la nota a vincular")

class TaskResponse(TaskBase):
    id: str
    user_id: str
    calendar_event_id: Optional[str]
    media_url: Optional[str]
    created_at: datetime
    updated_at: datetime
    tags: List[TagResponse] = []
    notes: List[NoteSummary] = []
    events: List[EventSummary] = []
    reminders_data: List[ReminderResponse] = Field(default=[], description="Lista de recordatorios generados")
    has_reminder: bool = False

    class Config:
        from_attributes = True

class TaskRelatedResponse(BaseModel):
    notes: List[NoteSummary] = []
    events: List[EventSummary] = []

class PaginatedTaskResponse(BaseModel):
    data: List[TaskResponse]
    next_cursor: Optional[str] = None
    has_more: bool = False
