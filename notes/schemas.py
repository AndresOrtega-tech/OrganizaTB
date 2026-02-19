from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

try:
    from backend.tags.schemas import TagResponse
except ImportError:
    from tags.schemas import TagResponse


class NoteBase(BaseModel):
    title: Optional[str] = Field(None, description="Título de la nota")
    content: Optional[str] = Field(None, description="Contenido de la nota", max_length=800)
    summary: Optional[str] = Field(None, description="Resumen de la nota generado por IA o manual", max_length=500)
    is_archived: bool = Field(False, description="Indica si la nota está archivada")


class NoteCreate(NoteBase):
    pass
    # media_url es null por ahora


class NoteUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = Field(None, max_length=800)
    summary: Optional[str] = Field(None, max_length=500)
    is_archived: Optional[bool] = None


class NoteAssignTag(BaseModel):
    tag_id: str = Field(..., description="ID de la etiqueta a asignar a la nota")


class NoteSummaryUpdate(BaseModel):
    summary: Optional[str] = Field(None, max_length=500)


class TaskSummary(BaseModel):
    id: str
    title: str
    is_completed: bool


class EventSummary(BaseModel):
    id: str
    title: str
    start_time: datetime


class NoteResponse(NoteBase):
    id: str
    user_id: str
    media_url: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class NoteRelatedResponse(BaseModel):
    tags: List[TagResponse]
    tasks: List[TaskSummary]
    events: List[EventSummary]
