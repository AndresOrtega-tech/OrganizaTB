from fastapi import APIRouter, HTTPException, status, Depends
import logging

try:
    from backend.database import supabase
    from backend.relations.schemas import TaskNoteLink, TaskEventLink, NoteEventLink
    from backend.auth.dependencies import get_current_user
except ImportError:
    from database import supabase
    from relations.schemas import TaskNoteLink, TaskEventLink, NoteEventLink
    from auth.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/task-note", status_code=status.HTTP_201_CREATED, summary="Vincular tarea y nota")
async def link_task_note(payload: TaskNoteLink, user=Depends(get_current_user)):
    try:
        user_id = user.id

        task_res = supabase.table("tasks").select("id").eq("id", payload.task_id).eq("user_id", user_id).execute()
        if not task_res.data:
            raise HTTPException(status_code=404, detail="Tarea no encontrada")

        note_res = supabase.table("notes").select("id").eq("id", payload.note_id).eq("user_id", user_id).execute()
        if not note_res.data:
            raise HTTPException(status_code=404, detail="Nota no encontrada")

        existing = (
            supabase.table("task_notes")
            .select("task_id")
            .eq("task_id", payload.task_id)
            .eq("note_id", payload.note_id)
            .execute()
        )
        if existing.data:
            raise HTTPException(status_code=409, detail="La vinculación ya existe")

        supabase.table("task_notes").insert(
            {"task_id": payload.task_id, "note_id": payload.note_id}
        ).execute()

        return {"message": "Tarea y nota vinculadas exitosamente"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error vinculando tarea y nota: {e}")
        raise HTTPException(status_code=400, detail="Error interno del servidor")


@router.delete(
    "/task-note", status_code=status.HTTP_200_OK, summary="Desvincular tarea y nota"
)
async def unlink_task_note(payload: TaskNoteLink, user=Depends(get_current_user)):
    try:
        user_id = user.id

        task_res = supabase.table("tasks").select("id").eq("id", payload.task_id).eq("user_id", user_id).execute()
        if not task_res.data:
            raise HTTPException(status_code=404, detail="Tarea no encontrada")

        note_res = supabase.table("notes").select("id").eq("id", payload.note_id).eq("user_id", user_id).execute()
        if not note_res.data:
            raise HTTPException(status_code=404, detail="Nota no encontrada")

        existing = (
            supabase.table("task_notes")
            .select("task_id")
            .eq("task_id", payload.task_id)
            .eq("note_id", payload.note_id)
            .execute()
        )
        if not existing.data:
            raise HTTPException(status_code=404, detail="La vinculación no existe")

        supabase.table("task_notes").delete().eq("task_id", payload.task_id).eq(
            "note_id", payload.note_id
        ).execute()

        return {"message": "Vinculación entre tarea y nota eliminada exitosamente"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error desvinculando tarea y nota: {e}")
        raise HTTPException(status_code=400, detail="Error interno del servidor")


@router.post("/task-event", status_code=status.HTTP_201_CREATED, summary="Vincular tarea y evento")
async def link_task_event(payload: TaskEventLink, user=Depends(get_current_user)):
    try:
        user_id = user.id

        task_res = supabase.table("tasks").select("id").eq("id", payload.task_id).eq("user_id", user_id).execute()
        if not task_res.data:
            raise HTTPException(status_code=404, detail="Tarea no encontrada")

        event_res = supabase.table("events").select("id").eq("id", payload.event_id).eq("user_id", user_id).execute()
        if not event_res.data:
            raise HTTPException(status_code=404, detail="Evento no encontrado")

        existing = (
            supabase.table("event_tasks")
            .select("event_id")
            .eq("event_id", payload.event_id)
            .eq("task_id", payload.task_id)
            .execute()
        )
        if existing.data:
            raise HTTPException(status_code=409, detail="La vinculación ya existe")

        supabase.table("event_tasks").insert(
            {"event_id": payload.event_id, "task_id": payload.task_id}
        ).execute()

        return {"message": "Tarea y evento vinculados exitosamente"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error vinculando tarea y evento: {e}")
        raise HTTPException(status_code=400, detail="Error interno del servidor")


@router.delete(
    "/task-event",
    status_code=status.HTTP_200_OK,
    summary="Desvincular tarea y evento",
)
async def unlink_task_event(payload: TaskEventLink, user=Depends(get_current_user)):
    try:
        user_id = user.id

        task_res = supabase.table("tasks").select("id").eq("id", payload.task_id).eq("user_id", user_id).execute()
        if not task_res.data:
            raise HTTPException(status_code=404, detail="Tarea no encontrada")

        event_res = supabase.table("events").select("id").eq("id", payload.event_id).eq("user_id", user_id).execute()
        if not event_res.data:
            raise HTTPException(status_code=404, detail="Evento no encontrado")

        existing = (
            supabase.table("event_tasks")
            .select("event_id")
            .eq("event_id", payload.event_id)
            .eq("task_id", payload.task_id)
            .execute()
        )
        if not existing.data:
            raise HTTPException(status_code=404, detail="La vinculación no existe")

        supabase.table("event_tasks").delete().eq("event_id", payload.event_id).eq(
            "task_id", payload.task_id
        ).execute()

        return {"message": "Vinculación entre tarea y evento eliminada exitosamente"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error desvinculando tarea y evento: {e}")
        raise HTTPException(status_code=400, detail="Error interno del servidor")


@router.post("/note-event", status_code=status.HTTP_201_CREATED, summary="Vincular nota y evento")
async def link_note_event(payload: NoteEventLink, user=Depends(get_current_user)):
    try:
        user_id = user.id

        note_res = supabase.table("notes").select("id").eq("id", payload.note_id).eq("user_id", user_id).execute()
        if not note_res.data:
            raise HTTPException(status_code=404, detail="Nota no encontrada")

        event_res = supabase.table("events").select("id").eq("id", payload.event_id).eq("user_id", user_id).execute()
        if not event_res.data:
            raise HTTPException(status_code=404, detail="Evento no encontrado")

        existing = (
            supabase.table("event_notes")
            .select("event_id")
            .eq("event_id", payload.event_id)
            .eq("note_id", payload.note_id)
            .execute()
        )
        if existing.data:
            raise HTTPException(status_code=409, detail="La vinculación ya existe")

        supabase.table("event_notes").insert(
            {"event_id": payload.event_id, "note_id": payload.note_id}
        ).execute()

        return {"message": "Nota y evento vinculados exitosamente"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error vinculando nota y evento: {e}")
        raise HTTPException(status_code=400, detail="Error interno del servidor")


@router.delete(
    "/note-event",
    status_code=status.HTTP_200_OK,
    summary="Desvincular nota y evento",
)
async def unlink_note_event(payload: NoteEventLink, user=Depends(get_current_user)):
    try:
        user_id = user.id

        note_res = supabase.table("notes").select("id").eq("id", payload.note_id).eq("user_id", user_id).execute()
        if not note_res.data:
            raise HTTPException(status_code=404, detail="Nota no encontrada")

        event_res = supabase.table("events").select("id").eq("id", payload.event_id).eq("user_id", user_id).execute()
        if not event_res.data:
            raise HTTPException(status_code=404, detail="Evento no encontrado")

        existing = (
            supabase.table("event_notes")
            .select("event_id")
            .eq("event_id", payload.event_id)
            .eq("note_id", payload.note_id)
            .execute()
        )
        if not existing.data:
            raise HTTPException(status_code=404, detail="La vinculación no existe")

        supabase.table("event_notes").delete().eq("event_id", payload.event_id).eq(
            "note_id", payload.note_id
        ).execute()

        return {"message": "Vinculación entre nota y evento eliminada exitosamente"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error desvinculando nota y evento: {e}")
        raise HTTPException(status_code=400, detail="Error interno del servidor")

