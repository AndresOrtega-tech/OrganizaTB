from pydantic import BaseModel, Field, validator
from typing import Optional
import re

class TagBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50, description="Nombre de la etiqueta")
    color: Optional[str] = Field(default="#808080", description="Color en formato Hex (ej. #RRGGBB)")

    @validator("color")
    def validate_hex_color(cls, v):
        if v is None:
            return "#808080"
        # Regex para validar color Hex (#RRGGBB o #RGB)
        regex = r"^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$"
        if not re.match(regex, v):
            raise ValueError("El color debe estar en formato Hex válido (ej. #FF0000)")
        return v

class TagCreate(TagBase):
    pass
    # icon se omite aquí porque se manejará como null internamente por ahora

class TagUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    color: Optional[str] = None
    icon: Optional[str] = Field(None, description="Icono de la etiqueta")

    @validator("color")
    def validate_hex_color(cls, v):
        if v is None:
            return v
        regex = r"^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$"
        if not re.match(regex, v):
            raise ValueError("El color debe estar en formato Hex válido (ej. #FF0000)")
        return v

class TagResponse(TagBase):
    id: str
    user_id: str
    icon: Optional[str] = None
    created_at: str

    class Config:
        from_attributes = True
