from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional
import uuid
from datetime import datetime, timedelta

try:
    from backend.database import supabase
    from backend.events.schemas import (
        EventCreate, 
        EventUpdate, 
        EventResponse, 
        EventRelatedResponse,
        EventAssignTag
    )
    from backend.tasks.schemas import ReminderConfig
    from backend.auth.dependencies import get_current_user
except ImportError:
    from database import supabase
    from events.schemas import (
        EventCreate, 
        EventUpdate, 
        EventResponse, 
        EventRelatedResponse,
        EventAssignTag
    )
    from tasks.schemas import ReminderConfig
    from auth.dependencies import get_current_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

def calculate_remind_at(target_date: datetime, reminder: ReminderConfig) -> datetime:
    delta = timedelta()
    if reminder.unit == "minutes":
        delta = timedelta(minutes=reminder.value)
    elif reminder.unit == "hours":
        delta = timedelta(hours=reminder.value)
    elif reminder.unit == "days":
        delta = timedelta(days=reminder.value)
    return target_date - delta

@router.post("/", response_model=EventResponse, status_code=status.HTTP_201_CREATED, summary="Crear nuevo evento")
async def create_event(event: EventCreate, user=Depends(get_current_user)):
    try:
        user_id = user.id
        event_id = str(uuid.uuid4())
        
        event_data = event.dict(exclude={"reminders"})
        event_data["id"] = event_id
        event_data["user_id"] = user_id
        
        # Convertir datetimes
        event_data["start_time"] = event_data["start_time"].isoformat()
        event_data["end_time"] = event_data["end_time"].isoformat()
        
        if event.reminders:
            event_data["has_reminder"] = True
            
        # Insertar evento
        response = supabase.table("events").insert(event_data).execute()
        if not response.data:
            raise HTTPException(status_code=500, detail="No se pudo crear el evento")
            
        created_event = response.data[0]
        
        # Procesar recordatorios
        reminders_response = []
        if event.reminders:
            reminders_to_insert = []
            for rem in event.reminders:
                remind_at = calculate_remind_at(event.start_time, rem)
                reminders_to_insert.append({
                    "user_id": user_id,
                    "event_id": event_id,  # Columna nueva en reminders
                    "remind_at": remind_at.isoformat(),
                    "status": "pending"
                })
            if reminders_to_insert:
                rem_res = supabase.table("reminders").insert(reminders_to_insert).execute()
                reminders_response = rem_res.data or []
                
        created_event["reminders_data"] = reminders_response
        return created_event
        
    except Exception as e:
        logger.error(f"Error creando evento: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=List[EventResponse], summary="Listar eventos")
async def list_events(
    user=Depends(get_current_user),
    start_date: Optional[datetime] = Query(None, description="Filtrar eventos desde esta fecha"),
    end_date: Optional[datetime] = Query(None, description="Filtrar eventos hasta esta fecha")
):
    try:
        query = supabase.table("events").select("*, reminders(*), event_tags(tags(id, name, color, icon))").eq("user_id", user.id)
        
        if start_date:
            query = query.gte("start_time", start_date.isoformat())
        if end_date:
            query = query.lte("end_time", end_date.isoformat())
            
        response = query.execute()
        events = response.data
        
        # Cargar recordatorios (ya vienen en el join)
        for event in events:
            if "reminders" in event:
                event["reminders_data"] = event["reminders"]
                del event["reminders"]
            else:
                event["reminders_data"] = []
                
            # Procesar etiquetas vinculadas
            tags_list = []
            if "event_tags" in event:
                for item in event["event_tags"]:
                    if isinstance(item, dict) and item.get("tags"):
                        tags_list.append(item["tags"])
                del event["event_tags"]
            event["tags"] = tags_list
            
        return events
    except Exception as e:
        logger.error(f"Error listando eventos: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{event_id}", response_model=EventResponse)
async def get_event(event_id: str, user=Depends(get_current_user)):
    try:
        res = supabase.table("events").select("*, reminders(*), event_tags(tags(id, name, color, icon))").eq("id", event_id).eq("user_id", user.id).execute()
        if not res.data:
            raise HTTPException(status_code=404, detail="Evento no encontrado")
            
        event = res.data[0]
        
        if "reminders" in event:
            event["reminders_data"] = event["reminders"]
            del event["reminders"]
        else:
            event["reminders_data"] = []

        # Procesar etiquetas vinculadas
        tags_list = []
        if "event_tags" in event:
            for item in event["event_tags"]:
                if isinstance(item, dict) and item.get("tags"):
                    tags_list.append(item["tags"])
            del event["event_tags"]
        event["tags"] = tags_list

        return event
    except Exception as e:
        logger.error(f"Error obteniendo evento: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.patch("/{event_id}", response_model=EventResponse)
async def update_event(event_id: str, update: EventUpdate, user=Depends(get_current_user)):
    try:
        update_data = {k: v for k, v in update.dict(exclude={"reminders"}).items() if v is not None}
        
        # Obtener evento actual para lógica de fechas
        curr_res = supabase.table("events").select("start_time").eq("id", event_id).eq("user_id", user.id).execute()
        if not curr_res.data:
            raise HTTPException(status_code=404, detail="Evento no encontrado")
        current_start = curr_res.data[0]["start_time"]
        
        new_start_str = update_data.get("start_time", current_start)
        if isinstance(new_start_str, datetime):
            new_start_str = new_start_str.isoformat()
            update_data["start_time"] = new_start_str
            
        if "end_time" in update_data:
            update_data["end_time"] = update_data["end_time"].isoformat()

        # Manejo de recordatorios
        if update.reminders is not None:
            # Borrar anteriores
            supabase.table("reminders").delete().eq("event_id", event_id).execute()
            
            if update.reminders:
                start_obj = datetime.fromisoformat(str(new_start_str).replace("Z", "+00:00"))
                rems = []
                for r in update.reminders:
                    at = calculate_remind_at(start_obj, r)
                    rems.append({
                        "user_id": user.id,
                        "event_id": event_id,
                        "remind_at": at.isoformat(),
                        "status": "pending"
                    })
                supabase.table("reminders").insert(rems).execute()
                update_data["has_reminder"] = True
            else:
                update_data["has_reminder"] = False
                
        if update_data:
            update_data["updated_at"] = datetime.now().isoformat()
            res = supabase.table("events").update(update_data).eq("id", event_id).execute()
            updated_event = res.data[0]
        else:
            res = supabase.table("events").select("*").eq("id", event_id).execute()
            updated_event = res.data[0]
            
        rem_res = supabase.table("reminders").select("*").eq("event_id", event_id).execute()
        updated_event["reminders_data"] = rem_res.data or []
        
        return updated_event
        
    except Exception as e:
        logger.error(f"Error actualizando evento: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{event_id}", status_code=204)
async def delete_event(event_id: str, user=Depends(get_current_user)):
    try:
        res = supabase.table("events").delete().eq("id", event_id).eq("user_id", user.id).execute()
        if not res.data:
            raise HTTPException(status_code=404, detail="Evento no encontrado")
    except Exception as e:
        logger.error(f"Error eliminando evento: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{event_id}/related", response_model=EventRelatedResponse, summary="Obtener relaciones de un evento")
async def get_event_related(event_id: str, user=Depends(get_current_user)):
    try:
        # 1. Verificar que el evento pertenece al usuario
        event_check = supabase.table("events").select("id").eq("id", event_id).eq("user_id", user.id).execute()
        if not event_check.data:
            raise HTTPException(status_code=404, detail="Evento no encontrado")

        # 2. Tags: event_tags → tags
        tags_res = supabase.table("event_tags").select("tags(id, name, color, icon)").eq("event_id", event_id).execute()
        tags = [item["tags"] for item in tags_res.data if item.get("tags")]

        # 3. Tasks: event_tasks → tasks
        tasks_res = supabase.table("event_tasks").select("tasks(id, title, is_completed)").eq("event_id", event_id).execute()
        tasks = [item["tasks"] for item in tasks_res.data if item.get("tasks")]

        # 4. Notes: event_notes → notes
        notes_res = supabase.table("event_notes").select("notes(id, title)").eq("event_id", event_id).execute()
        notes = [item["notes"] for item in notes_res.data if item.get("notes")]

        return EventRelatedResponse(tags=tags, tasks=tasks, notes=notes)

    except Exception as e:
        logger.error(f"Error obteniendo relaciones del evento: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{event_id}/tags", status_code=status.HTTP_200_OK, summary="Asignar etiqueta a un evento")
async def assign_tag_to_event(event_id: str, body: EventAssignTag, user=Depends(get_current_user)):
    try:
        # 1. Verificar que el evento pertenece al usuario
        event_check = supabase.table("events").select("id").eq("id", event_id).eq("user_id", user.id).execute()
        if not event_check.data:
            raise HTTPException(status_code=404, detail="Evento no encontrado")

        # 2. Verificar que el tag pertenece al usuario (se asume que existe en BD, el UPSERT fallaría si no por FK, pero es mejor validarlo rápido)
        tag_check = supabase.table("tags").select("id").eq("id", body.tag_id).eq("user_id", user.id).execute()
        if not tag_check.data:
            raise HTTPException(status_code=404, detail="Etiqueta no encontrada")

        # 3. Insertar en event_tags
        supabase.table("event_tags").upsert(
            {"event_id": event_id, "tag_id": body.tag_id},
            ignore_duplicates=True
        ).execute()

        return {"message": "Etiqueta asignada correctamente", "assigned": 1}

    except Exception as e:
        logger.error(f"Error asignando etiqueta a evento: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{event_id}/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Desvincular etiqueta de evento")
async def remove_tag_from_event(event_id: str, tag_id: str, user=Depends(get_current_user)):
    try:
        # Verificar que el evento pertenece al usuario
        event_check = supabase.table("events").select("id").eq("id", event_id).eq("user_id", user.id).execute()
        if not event_check.data:
            raise HTTPException(status_code=404, detail="Evento no encontrado")

        # Eliminar de event_tags
        supabase.table("event_tags").delete().eq("event_id", event_id).eq("tag_id", tag_id).execute()

    except Exception as e:
        logger.error(f"Error desvinculando etiqueta de evento: {e}")
        raise HTTPException(status_code=400, detail=str(e))
