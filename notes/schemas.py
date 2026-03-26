from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

try:
    from backend.tags.schemas import TagSummary
except ImportError:
    from tags.schemas import TagSummary


class NoteBase(BaseModel):
    title: Optional[str] = Field(None, max_length=80, description="Título de la nota")
    content: Optional[str] = Field(
        None, description="Contenido de la nota", max_length=800
    )
    summary: Optional[str] = Field(
        None, description="Resumen de la nota generado por IA o manual", max_length=500
    )
    is_archived: bool = Field(False, description="Indica si la nota está archivada")


class NoteCreate(NoteBase):
    pass
    # media_url es null por ahora


class NoteUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=80)
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
    tags: List[TagSummary] = Field(
        default=[], description="Etiquetas vinculadas a la nota"
    )

    class Config:
        from_attributes = True


class NoteRelatedResponse(BaseModel):
    tags: List[TagSummary]
    tasks: List[TaskSummary]
    events: List[EventSummary]
