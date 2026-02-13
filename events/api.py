from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional
import uuid
from datetime import datetime, timedelta

try:
    from backend.database import supabase
    from backend.events.schemas import EventCreate, EventUpdate, EventResponse, EventLinkTask, EventLinkNote, EventAssignTags
    from backend.tasks.schemas import ReminderConfig
    from backend.auth.dependencies import get_current_user
except ImportError:
    from database import supabase
    from events.schemas import EventCreate, EventUpdate, EventResponse, EventLinkTask, EventLinkNote, EventAssignTags
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
    end_date: Optional[datetime] = Query(None, description="Filtrar eventos hasta esta fecha"),
    tag_ids: Optional[List[str]] = Query(None, description="Filtrar por etiquetas (AND)")
):
    try:
        # Join con event_tags para filtrar o mostrar
        select_query = "*, reminders(*), event_tasks(tasks(id, title, is_completed)), event_notes(notes(id, title)), event_tags(tags(*))"
        if tag_ids:
            select_query = "*, reminders(*), event_tasks(tasks(id, title, is_completed)), event_notes(notes(id, title)), event_tags!inner(tags(*))"

        query = supabase.table("events").select(select_query).eq("user_id", user.id)
        
        if start_date:
            query = query.gte("start_time", start_date.isoformat())
        if end_date:
            query = query.lte("end_time", end_date.isoformat())
            
        if tag_ids:
            query = query.in_("event_tags.tag_id", tag_ids)

        response = query.execute()
        events = response.data
        
        final_events = []
        required_tag_ids = set(tag_ids) if tag_ids else set()

        # Cargar recordatorios (ya vienen en el join)
        for event in events:
            if "reminders" in event:
                event["reminders_data"] = event["reminders"]
                del event["reminders"]
            else:
                event["reminders_data"] = []
            
            # Process linked tasks
            tasks_list = []
            if "event_tasks" in event:
                for item in event["event_tasks"]:
                    if item.get("tasks"):
                        tasks_list.append(item["tasks"])
                del event["event_tasks"]
            event["tasks"] = tasks_list

            # Process linked notes
            notes_list = []
            if "event_notes" in event:
                for item in event["event_notes"]:
                    if item.get("notes"):
                        notes_list.append(item["notes"])
                del event["event_notes"]
            event["notes"] = notes_list
            
            # Process tags
            tags_list = []
            found_tag_ids = set()
            if "event_tags" in event:
                for item in event["event_tags"]:
                    if item.get("tags"):
                        tag_data = item["tags"]
                        tags_list.append(tag_data)
                        found_tag_ids.add(str(tag_data.get("id")))
                del event["event_tags"]
            event["tags"] = tags_list

            if tag_ids:
                if required_tag_ids.issubset(found_tag_ids):
                    final_events.append(event)
            else:
                final_events.append(event)
            
        return final_events
    except Exception as e:
        logger.error(f"Error listando eventos: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{event_id}", response_model=EventResponse)
async def get_event(event_id: str, user=Depends(get_current_user)):
    try:
        res = supabase.table("events").select("*, reminders(*), event_tasks(tasks(id, title, is_completed)), event_notes(notes(id, title)), event_tags(tags(*))").eq("id", event_id).eq("user_id", user.id).execute()
        if not res.data:
            raise HTTPException(status_code=404, detail="Evento no encontrado")
            
        event = res.data[0]
        
        if "reminders" in event:
            event["reminders_data"] = event["reminders"]
            del event["reminders"]
        else:
            event["reminders_data"] = []

        # Process linked tasks
        tasks_list = []
        if "event_tasks" in event:
            for item in event["event_tasks"]:
                if item.get("tasks"):
                    tasks_list.append(item["tasks"])
            del event["event_tasks"]
        event["tasks"] = tasks_list

        # Process linked notes
        notes_list = []
        if "event_notes" in event:
            for item in event["event_notes"]:
                if item.get("notes"):
                    notes_list.append(item["notes"])
            del event["event_notes"]
        event["notes"] = notes_list
        
        # Process tags
        tags_list = []
        if "event_tags" in event:
            for item in event["event_tags"]:
                if item.get("tags"):
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

# Relaciones
@router.post("/tags", status_code=status.HTTP_200_OK, summary="Asignar etiquetas a un evento")
async def assign_tags_to_event(assignment: EventAssignTags, user=Depends(get_current_user)):
    """
    Asigna una o más etiquetas a un evento existente.
    """
    try:
        user_id = user.id
        event_id = assignment.event_id
        tag_ids = assignment.tag_ids

        # 1. Verificar que el evento pertenece al usuario
        event_check = supabase.table("events").select("id").eq("id", event_id).eq("user_id", user_id).execute()
        if not event_check.data:
            raise HTTPException(status_code=404, detail="Evento no encontrado")

        if not tag_ids:
            return {"message": "No se proporcionaron etiquetas para asignar"}

        # 2. Preparar datos para inserción en event_tags
        data_to_insert = [{"event_id": event_id, "tag_id": tag_id} for tag_id in tag_ids]
        
        # Upsert
        response = supabase.table("event_tags").upsert(data_to_insert, on_conflict="event_id, tag_id", ignore_duplicates=True).execute()

        return {"message": "Etiquetas asignadas correctamente", "assigned_count": len(tag_ids)}

    except Exception as e:
        logger.error(f"Error asignando etiquetas a evento: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{event_id}/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Desvincular etiqueta de evento")
async def remove_tag_from_event(event_id: str, tag_id: str, user=Depends(get_current_user)):
    """
    Elimina la asociación entre un evento y una etiqueta.
    """
    try:
        user_id = user.id

        # 1. Verificar que el evento pertenece al usuario
        event_check = supabase.table("events").select("id").eq("id", event_id).eq("user_id", user_id).execute()
        if not event_check.data:
            raise HTTPException(status_code=404, detail="Evento no encontrado")

        # 2. Eliminar la relación
        response = supabase.table("event_tags").delete().eq("event_id", event_id).eq("tag_id", tag_id).execute()

        return None

    except Exception as e:
        logger.error(f"Error desvinculando etiqueta de evento: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/tasks", status_code=201)
async def link_task(link: EventLinkTask, user=Depends(get_current_user)):
    try:
        # Validar propiedad
        e_check = supabase.table("events").select("id").eq("id", link.event_id).eq("user_id", user.id).execute()
        t_check = supabase.table("tasks").select("id").eq("id", link.task_id).eq("user_id", user.id).execute()
        
        if not e_check.data or not t_check.data:
            raise HTTPException(status_code=404, detail="Evento o Tarea no encontrados")
            
        supabase.table("event_tasks").upsert({
            "event_id": link.event_id,
            "task_id": link.task_id
        }, ignore_duplicates=True).execute()
        
        return {"message": "Vinculado correctamente"}
    except Exception as e:
        logger.error(f"Error vinculando tarea: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{event_id}/tasks/{task_id}", status_code=204)
async def unlink_task(event_id: str, task_id: str, user=Depends(get_current_user)):
    try:
        # Validar propiedad del evento (la tarea se valida por cascada o consistencia, pero mejor validar)
        e_check = supabase.table("events").select("id").eq("id", event_id).eq("user_id", user.id).execute()
        if not e_check.data:
             raise HTTPException(status_code=404, detail="Evento no encontrado")

        supabase.table("event_tasks").delete().eq("event_id", event_id).eq("task_id", task_id).execute()
    except Exception as e:
        logger.error(f"Error desvinculando tarea: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/notes", status_code=201)
async def link_note(link: EventLinkNote, user=Depends(get_current_user)):
    try:
        e_check = supabase.table("events").select("id").eq("id", link.event_id).eq("user_id", user.id).execute()
        n_check = supabase.table("notes").select("id").eq("id", link.note_id).eq("user_id", user.id).execute()
        
        if not e_check.data or not n_check.data:
            raise HTTPException(status_code=404, detail="Evento o Nota no encontrados")
            
        supabase.table("event_notes").upsert({
            "event_id": link.event_id,
            "note_id": link.note_id
        }, ignore_duplicates=True).execute()
        
        return {"message": "Vinculado correctamente"}
    except Exception as e:
        logger.error(f"Error vinculando nota: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{event_id}/notes/{note_id}", status_code=204)
async def unlink_note(event_id: str, note_id: str, user=Depends(get_current_user)):
    try:
        e_check = supabase.table("events").select("id").eq("id", event_id).eq("user_id", user.id).execute()
        if not e_check.data:
             raise HTTPException(status_code=404, detail="Evento no encontrado")

        supabase.table("event_notes").delete().eq("event_id", event_id).eq("note_id", note_id).execute()
    except Exception as e:
        logger.error(f"Error desvinculando nota: {e}")
        raise HTTPException(status_code=400, detail=str(e))
