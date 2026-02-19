from pydantic import BaseModel, Field, validator
from typing import Optional, List, Literal
from datetime import datetime

class ReminderConfig(BaseModel):
    value: int = Field(..., gt=0, description="Cantidad de tiempo antes del vencimiento")
    unit: Literal["minutes", "hours", "days"] = Field(..., description="Unidad de tiempo (minutes, hours, days)")

class ReminderResponse(BaseModel):
    id: str
    remind_at: datetime
    status: str

class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, description="Título de la tarea")
    description: Optional[str] = Field(None, description="Descripción detallada de la tarea", max_length=500)
    due_date: Optional[datetime] = Field(None, description="Fecha límite de la tarea")
    is_completed: bool = Field(False, description="Estado de completado de la tarea")
    priority: Literal["baja", "media", "alta"] = Field("media", description="Prioridad de la tarea")

class TaskCreate(TaskBase):
    reminders: Optional[List[ReminderConfig]] = Field(None, description="Configuración de recordatorios (tiempo antes del vencimiento)")

class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1)
    description: Optional[str] = Field(None, max_length=500)
    due_date: Optional[datetime] = None
    is_completed: Optional[bool] = None
    priority: Optional[Literal["baja", "media", "alta"]] = None
    reminders: Optional[List[ReminderConfig]] = Field(None, description="Nueva lista de recordatorios (reemplaza los existentes)")

class TaskAssignTags(BaseModel):
    tag_id: str = Field(..., description="ID de la etiqueta a asignar")

class TaskCreateResponse(TaskBase):
    id: str
    user_id: str
    calendar_event_id: Optional[str]
    media_url: Optional[str]
    created_at: datetime
    updated_at: datetime
    reminders_data: List[ReminderResponse] = Field(default=[], description="Lista de recordatorios generados")
    has_reminder: bool = False

    class Config:
        from_attributes = True

class TaskResponse(TaskBase):
    id: str
    user_id: str
    calendar_event_id: Optional[str]
    media_url: Optional[str]
    created_at: datetime
    updated_at: datetime
    reminders_data: List[ReminderResponse] = Field(default=[], description="Lista de recordatorios generados")
    has_reminder: bool = False

    class Config:
        from_attributes = True

class TaskRelatedTag(BaseModel):
    id: str
    name: str
    color: Optional[str] = None
    icon: Optional[str] = None

class TaskRelatedNote(BaseModel):
    id: str
    title: Optional[str] = None
    content: Optional[str] = None

class TaskRelatedEvent(BaseModel):
    id: str
    title: str
    start_time: datetime

class TaskRelatedResponse(BaseModel):
    tags: List[TaskRelatedTag] = []
    notes: List[TaskRelatedNote] = []
    events: List[TaskRelatedEvent] = []

class PaginatedTaskResponse(BaseModel):
    data: List[TaskResponse]
    next_cursor: Optional[datetime] = None
    has_more: bool = False
