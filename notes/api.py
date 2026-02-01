from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional, Set
import uuid
from datetime import datetime
try:
    from backend.database import supabase
    from backend.notes.schemas import NoteCreate, NoteUpdate, NoteResponse, NoteAssignTags
    from backend.auth.dependencies import get_current_user
except ImportError:
    from database import supabase
    from notes.schemas import NoteCreate, NoteUpdate, NoteResponse, NoteAssignTags
    from auth.dependencies import get_current_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/", response_model=NoteResponse, status_code=status.HTTP_201_CREATED, summary="Crear una nueva nota")
async def create_note(note: NoteCreate, user=Depends(get_current_user)):
    try:
        user_id = user.id
        note_id = str(uuid.uuid4())
        
        note_data = note.dict()
        note_data["id"] = note_id
        note_data["user_id"] = user_id
        note_data["media_url"] = None 

        response = supabase.table("notes").insert(note_data).execute()
        
        if not response.data:
            raise HTTPException(status_code=500, detail="No se pudo crear la nota.")
            
        return response.data[0]

    except Exception as e:
        logger.error(f"Error creando nota: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=List[NoteResponse], summary="Listar todas las notas del usuario")
async def list_notes(
    user=Depends(get_current_user),
    is_archived: Optional[bool] = Query(None, description="Filtrar por estado de archivado"),
    tag_ids: Optional[List[str]] = Query(None, description="Filtrar por etiquetas (AND: la nota debe tener TODAS las etiquetas seleccionadas)"),
    sort_by: str = Query("updated_at", pattern="^(updated_at)$", description="Ordenar por fecha de actualización"),
    order: str = Query("desc", pattern="^(asc|desc)$", description="Dirección del ordenamiento")
):
    try:
        user_id = user.id
        
        select_query = "*, note_tags(tags(*))"
        if tag_ids:
            select_query = "*, note_tags!inner(tags(*))"
            
        query = supabase.table("notes").select(select_query).eq("user_id", user_id)
        
        if is_archived is not None:
            query = query.eq("is_archived", is_archived)
            
        if tag_ids:
            query = query.in_("note_tags.tag_id", tag_ids)
            
        is_desc = (order == "desc")
        query = query.order("updated_at", desc=is_desc)
            
        response = query.execute()
        
        notes = response.data
        
        final_notes = []
        required_tag_ids = set(tag_ids) if tag_ids else set()

        for note in notes:
            tags_list = []
            found_tag_ids = set()
            
            if "note_tags" in note:
                for item in note["note_tags"]:
                    if item.get("tags"):
                        tag_data = item["tags"]
                        tags_list.append(tag_data)
                        found_tag_ids.add(str(tag_data.get("id")))

            note["tags"] = tags_list
            if "note_tags" in note:
                del note["note_tags"]
            
            if tag_ids:
                if required_tag_ids.issubset(found_tag_ids):
                    final_notes.append(note)
            else:
                final_notes.append(note)

        return final_notes
    except Exception as e:
        logger.error(f"Error listando notas: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{note_id}", response_model=NoteResponse, summary="Obtener una nota específica")
async def get_note(note_id: str, user=Depends(get_current_user)):
    try:
        user_id = user.id
        response = supabase.table("notes").select("*, note_tags(tags(*))").eq("id", note_id).eq("user_id", user_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Nota no encontrada")
            
        note = response.data[0]
        
        tags_list = []
        if "note_tags" in note:
            for item in note["note_tags"]:
                if item.get("tags"):
                    tags_list.append(item["tags"])
        note["tags"] = tags_list
        if "note_tags" in note:
            del note["note_tags"]
            
        return note
    except Exception as e:
        logger.error(f"Error obteniendo nota: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.patch("/{note_id}", response_model=NoteResponse, summary="Actualizar una nota")
async def update_note(note_id: str, note_update: NoteUpdate, user=Depends(get_current_user)):
    try:
        user_id = user.id
        
        update_data = {k: v for k, v in note_update.dict().items() if v is not None}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No se proporcionaron datos para actualizar")

        update_data["updated_at"] = datetime.now().isoformat()

        response = supabase.table("notes").update(update_data).eq("id", note_id).eq("user_id", user_id).execute()
        
        if not response.data:
             raise HTTPException(status_code=404, detail="Nota no encontrada o no tienes permiso para editarla")
             
        return response.data[0]
        
    except Exception as e:
        logger.error(f"Error actualizando nota: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Eliminar una nota")
async def delete_note(note_id: str, user=Depends(get_current_user)):
    try:
        user_id = user.id
        response = supabase.table("notes").delete().eq("id", note_id).eq("user_id", user_id).execute()
        
        if not response.data:
             raise HTTPException(status_code=404, detail="Nota no encontrada o no tienes permiso para eliminarla")
    except Exception as e:
        logger.error(f"Error eliminando nota: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/tags", status_code=status.HTTP_201_CREATED, summary="Asignar etiquetas a una nota")
async def assign_tags_to_note(assignment: NoteAssignTags, user=Depends(get_current_user)):
    try:
        user_id = user.id
        note_id = assignment.note_id
        tag_ids = assignment.tag_ids
        
        # Verificar que la nota pertenece al usuario
        note_check = supabase.table("notes").select("id").eq("id", note_id).eq("user_id", user_id).execute()
        if not note_check.data:
            raise HTTPException(status_code=404, detail="Nota no encontrada")
            
        # Preparar inserciones
        insert_data = [{"note_id": note_id, "tag_id": tag_id} for tag_id in tag_ids]
        
        response = supabase.table("note_tags").upsert(insert_data, on_conflict="note_id, tag_id").execute()
        
        return {"message": "Etiquetas asignadas correctamente"}
        
    except Exception as e:
        logger.error(f"Error asignando etiquetas a nota: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{note_id}/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Desvincular etiqueta de nota")
async def remove_tag_from_note(note_id: str, tag_id: str, user=Depends(get_current_user)):
    try:
        user_id = user.id
        
        # Verificar propiedad de la nota
        note_check = supabase.table("notes").select("id").eq("id", note_id).eq("user_id", user_id).execute()
        if not note_check.data:
             raise HTTPException(status_code=404, detail="Nota no encontrada")

        response = supabase.table("note_tags").delete().eq("note_id", note_id).eq("tag_id", tag_id).execute()
        
    except Exception as e:
        logger.error(f"Error desvinculando etiqueta de nota: {e}")
        raise HTTPException(status_code=400, detail=str(e))
