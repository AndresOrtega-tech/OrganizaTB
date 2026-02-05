from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

try:
    from backend.tags.schemas import TagResponse
except ImportError:
    from tags.schemas import TagResponse

class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, description="Título de la tarea")
    description: Optional[str] = Field(None, description="Descripción detallada de la tarea", max_length=500)
    due_date: Optional[datetime] = Field(None, description="Fecha límite de la tarea")
    has_reminder: bool = Field(False, description="Indica si la tarea tiene recordatorio activo")
    is_completed: bool = Field(False, description="Estado de completado de la tarea")

class TaskCreate(TaskBase):
    pass
    # calendar_event_id se generará automáticamente igual al ID de la tarea
    # media_url es null por ahora

class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1)
    description: Optional[str] = Field(None, max_length=500)
    due_date: Optional[datetime] = None
    is_completed: Optional[bool] = None
    has_reminder: Optional[bool] = None

class TaskAssignTags(BaseModel):
    task_id: str = Field(..., description="ID de la tarea a la que se asignarán las etiquetas")
    tag_ids: List[str] = Field(..., description="Lista de IDs de las etiquetas a asignar")

class TaskResponse(TaskBase):
    id: str
    user_id: str
    calendar_event_id: Optional[str]
    media_url: Optional[str]
    created_at: datetime
    updated_at: datetime
    tags: List[TagResponse] = []

    class Config:
        from_attributes = True
