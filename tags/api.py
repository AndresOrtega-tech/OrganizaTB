from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
try:
    from backend.database import supabase
    from backend.tags.schemas import TagCreate, TagUpdate, TagResponse
    from backend.auth.dependencies import get_current_user
except ImportError:
    from database import supabase
    from tags.schemas import TagCreate, TagUpdate, TagResponse
    from auth.dependencies import get_current_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/", response_model=TagResponse, status_code=status.HTTP_201_CREATED, summary="Crear una nueva etiqueta")
async def create_tag(tag: TagCreate, user=Depends(get_current_user)):
    """
    Crea una nueva etiqueta para el usuario autenticado.
    El nombre debe ser único para el usuario.
    """
    try:
        user_id = user.id
        
        # 1. Verificar si ya existe una etiqueta con el mismo nombre para este usuario
        existing_tag = supabase.table("tags").select("id").eq("user_id", user_id).eq("name", tag.name).execute()
        
        if existing_tag.data and len(existing_tag.data) > 0:
            raise HTTPException(
                status_code=400, 
                detail=f"Ya tienes una etiqueta con el nombre '{tag.name}'."
            )

        # 2. Insertar la nueva etiqueta
        # icon se fuerza a None por requerimiento actual
        tag_data = {
            "user_id": user_id,
            "name": tag.name,
            "color": tag.color,
            "icon": None 
        }
        
        response = supabase.table("tags").insert(tag_data).execute()
        
        if not response.data:
            raise HTTPException(status_code=500, detail="No se pudo crear la etiqueta.")
            
        return response.data[0]

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error creando etiqueta: {e}")
        raise HTTPException(status_code=400, detail="Error interno del servidor")

@router.get("/", response_model=List[TagResponse], summary="Listar todas las etiquetas del usuario")
async def list_tags(user=Depends(get_current_user)):
    """
    Obtiene todas las etiquetas creadas por el usuario autenticado.
    """
    try:
        user_id = user.id
        response = supabase.table("tags").select("*").eq("user_id", user_id).execute()
        return response.data
    except Exception as e:
        logger.error(f"Error listando etiquetas: {e}")
        raise HTTPException(status_code=400, detail="Error interno del servidor")

@router.patch("/{tag_id}", response_model=TagResponse, summary="Actualizar una etiqueta")
async def update_tag(tag_id: str, tag_update: TagUpdate, user=Depends(get_current_user)):
    """
    Actualiza el nombre o color de una etiqueta existente.
    """
    try:
        user_id = user.id
        
        # Filtrar campos que no son None
        update_data = {k: v for k, v in tag_update.dict().items() if v is not None}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No se proporcionaron datos para actualizar")
            
        # Verificar unicidad si se actualiza el nombre
        if "name" in update_data:
             existing_tag = supabase.table("tags").select("id").eq("user_id", user_id).eq("name", update_data["name"]).neq("id", tag_id).execute()
             if existing_tag.data:
                 raise HTTPException(status_code=400, detail=f"Ya tienes una etiqueta con el nombre '{update_data['name']}'.")

        # Ejecutar actualización asegurando que pertenezca al usuario
        response = supabase.table("tags").update(update_data).eq("id", tag_id).eq("user_id", user_id).execute()
        
        if not response.data:
             raise HTTPException(status_code=404, detail="Etiqueta no encontrada o no tienes permiso para editarla")
             
        return response.data[0]
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error actualizando etiqueta: {e}")
        raise HTTPException(status_code=400, detail="Error interno del servidor")

@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Eliminar una etiqueta")
async def delete_tag(tag_id: str, user=Depends(get_current_user)):
    """
    Elimina una etiqueta permanentemente.
    """
    try:
        user_id = user.id
        
        # Eliminar asegurando pertenencia
        response = supabase.table("tags").delete().eq("id", tag_id).eq("user_id", user_id).execute()
        
        # Supabase delete devuelve la fila eliminada en response.data
        if not response.data:
             raise HTTPException(status_code=404, detail="Etiqueta no encontrada o no tienes permiso para eliminarla")
             
        return None 
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error eliminando etiqueta: {e}")
        raise HTTPException(status_code=400, detail="Error interno del servidor")
