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
    is_archived: bool = Field(False, description="Indica si la nota está archivada")

class NoteCreate(NoteBase):
    pass
    # media_url es null por ahora

class NoteUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = Field(None, max_length=800)
    is_archived: Optional[bool] = None

class NoteAssignTags(BaseModel):
    note_id: str = Field(..., description="ID de la nota a la que se asignarán las etiquetas")
    tag_ids: List[str] = Field(..., description="Lista de IDs de las etiquetas a asignar")

class NoteResponse(NoteBase):
    id: str
    user_id: str
    media_url: Optional[str]
    created_at: datetime
    updated_at: datetime
    tags: List[TagResponse] = []

    class Config:
        from_attributes = True
