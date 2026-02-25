from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional, Set
import uuid
from datetime import datetime
try:
    from backend.database import supabase
    from backend.notes.schemas import (
        NoteCreate,
        NoteUpdate,
        NoteResponse,
        NoteAssignTag,
        NoteSummaryUpdate,
        NoteRelatedResponse,
    )
    from backend.auth.dependencies import get_current_user
except ImportError:
    from database import supabase
    from notes.schemas import (
        NoteCreate,
        NoteUpdate,
        NoteResponse,
        NoteAssignTag,
        NoteSummaryUpdate,
        NoteRelatedResponse,
    )
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
    order: str = Query("desc", pattern="^(asc|desc)$", description="Dirección del ordenamiento"),
    limit: Optional[int] = Query(None, ge=1, description="Límite de notas a retornar"),
):
    try:
        user_id = user.id

        # Siempre traemos tags; !inner solo para filtrar
        if tag_ids:
            select_query = "*, note_tags!inner(tags(id, name, color, icon))"
        else:
            select_query = "*, note_tags(tags(id, name, color, icon))"

        query = supabase.table("notes").select(select_query).eq("user_id", user_id)
        
        effective_archived = is_archived if is_archived is not None else False
        query = query.eq("is_archived", effective_archived)
            
        if tag_ids:
            query = query.in_("note_tags.tag_id", tag_ids)

        is_desc = order == "desc"
        query = query.order("updated_at", desc=is_desc)

        if limit is not None:
            query = query.limit(limit)

        response = query.execute()

        notes = response.data

        final_notes = []
        required_tag_ids = set(tag_ids) if tag_ids else set()

        for note in notes:
            found_tag_ids = set()
            tags_list = []

            if "note_tags" in note:
                for item in note["note_tags"]:
                    if item.get("tags"):
                        tag_data = item["tags"]
                        found_tag_ids.add(str(tag_data.get("id")))
                        tags_list.append(tag_data)
                del note["note_tags"]
            note["tags"] = tags_list

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
        response = (
            supabase.table("notes")
            .select("*")
            .eq("id", note_id)
            .eq("user_id", user_id)
            .execute()
        )

        if not response.data:
            raise HTTPException(status_code=404, detail="Nota no encontrada")

        return response.data[0]
    except Exception as e:
        logger.error(f"Error obteniendo nota: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.patch("/{note_id}", response_model=NoteResponse, summary="Actualizar una nota")
async def update_note(note_id: str, note_update: NoteUpdate, user=Depends(get_current_user)):
    try:
        user_id = user.id

        update_data = note_update.model_dump(exclude_unset=True)

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


@router.patch(
    "/{note_id}/summary",
    response_model=NoteResponse,
    summary="Actualizar resumen de una nota",
)
async def update_note_summary(
    note_id: str, summary_update: NoteSummaryUpdate, user=Depends(get_current_user)
):
    try:
        user_id = user.id

        update_data = {"summary": summary_update.summary}
        update_data["updated_at"] = datetime.now().isoformat()

        response = (
            supabase.table("notes")
            .update(update_data)
            .eq("id", note_id)
            .eq("user_id", user_id)
            .execute()
        )

        if not response.data:
            raise HTTPException(
                status_code=404,
                detail="Nota no encontrada o no tienes permiso para editarla",
            )

        return response.data[0]
    except Exception as e:
        logger.error(f"Error actualizando resumen de nota: {e}")
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

@router.post(
    "/{note_id}/tags",
    status_code=status.HTTP_200_OK,
    summary="Asignar etiqueta a una nota",
)
async def assign_tag_to_note(
    note_id: str, assignment: NoteAssignTag, user=Depends(get_current_user)
):
    try:
        user_id = user.id
        tag_id = assignment.tag_id

        note_check = (
            supabase.table("notes")
            .select("id")
            .eq("id", note_id)
            .eq("user_id", user_id)
            .execute()
        )
        if not note_check.data:
            raise HTTPException(status_code=404, detail="Nota no encontrada")

        existing = (
            supabase.table("note_tags")
            .select("note_id")
            .eq("note_id", note_id)
            .eq("tag_id", tag_id)
            .execute()
        )

        if existing.data:
            return {"message": "Etiqueta asignada correctamente", "assigned": 0}

        response = (
            supabase.table("note_tags")
            .insert({"note_id": note_id, "tag_id": tag_id})
            .execute()
        )

        if not response.data:
            raise HTTPException(
                status_code=500, detail="No se pudo asignar la etiqueta a la nota"
            )

        return {"message": "Etiqueta asignada correctamente", "assigned": 1}

    except Exception as e:
        logger.error(f"Error asignando etiquetas a nota: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{note_id}/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Desvincular etiqueta de nota")
async def remove_tag_from_note(note_id: str, tag_id: str, user=Depends(get_current_user)):
    try:
        user_id = user.id
        
        note_check = (
            supabase.table("notes")
            .select("id")
            .eq("id", note_id)
            .eq("user_id", user_id)
            .execute()
        )
        if not note_check.data:
             raise HTTPException(status_code=404, detail="Nota no encontrada")

        response = supabase.table("note_tags").delete().eq("note_id", note_id).eq("tag_id", tag_id).execute()

    except Exception as e:
        logger.error(f"Error desvinculando etiqueta de nota: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/{note_id}/related",
    response_model=NoteRelatedResponse,
    summary="Obtener relaciones de una nota",
)
async def get_note_related(note_id: str, user=Depends(get_current_user)):
    try:
        user_id = user.id

        response = (
            supabase.table("notes")
            .select(
                "note_tags(tags(id, name, color, icon)), "
                "task_notes(tasks(id, title, is_completed)), "
                "event_notes(events(id, title, start_time))"
            )
            .eq("id", note_id)
            .eq("user_id", user_id)
            .execute()
        )

        if not response.data:
            raise HTTPException(status_code=404, detail="Nota no encontrada")

        note = response.data[0]

        tags: List[dict] = []
        if "note_tags" in note:
            for item in note["note_tags"]:
                if item.get("tags"):
                    tags.append(item["tags"])

        tasks: List[dict] = []
        if "task_notes" in note:
            for item in note["task_notes"]:
                if item.get("tasks"):
                    tasks.append(item["tasks"])

        events: List[dict] = []
        if "event_notes" in note:
            for item in note["event_notes"]:
                if item.get("events"):
                    events.append(item["events"])

        return {
            "tags": tags,
            "tasks": tasks,
            "events": events,
        }
    except Exception as e:
        logger.error(f"Error obteniendo relaciones de nota: {e}")
        raise HTTPException(status_code=400, detail=str(e))
