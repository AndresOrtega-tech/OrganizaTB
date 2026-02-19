from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional
import uuid
from datetime import datetime, timedelta, timezone

try:
    from backend.database import supabase
    from backend.tasks.schemas import TaskCreate, TaskUpdate, TaskResponse, TaskAssignTags, ReminderConfig, TaskLinkNote, PaginatedTaskResponse, TaskRelatedResponse
    from backend.auth.dependencies import get_current_user
except ImportError:
    from database import supabase
    from tasks.schemas import TaskCreate, TaskUpdate, TaskResponse, TaskAssignTags, ReminderConfig, TaskLinkNote, PaginatedTaskResponse, TaskRelatedResponse
    from auth.dependencies import get_current_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

def calculate_remind_at(due_date: datetime, reminder: ReminderConfig) -> datetime:
    delta = timedelta()
    if reminder.unit == "minutes":
        delta = timedelta(minutes=reminder.value)
    elif reminder.unit == "hours":
        delta = timedelta(hours=reminder.value)
    elif reminder.unit == "days":
        delta = timedelta(days=reminder.value)
    
    return due_date - delta

@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED, summary="Crear una nueva tarea")
async def create_task(task: TaskCreate, user=Depends(get_current_user)):
    """
    Crea una nueva tarea para el usuario autenticado.
    El ID de la tarea se genera automáticamente y se asigna también como calendar_event_id.
    Si se proporcionan recordatorios y fecha límite, se crean las entradas en la tabla reminders.
    """
    try:
        user_id = user.id
        
        # Generar UUID explícitamente para asignarlo a calendar_event_id
        task_id = str(uuid.uuid4())
        
        task_data = task.dict(exclude={"reminders"})
        task_data["id"] = task_id
        task_data["user_id"] = user_id
        task_data["calendar_event_id"] = task_id # Mismo que el ID
        task_data["media_url"] = None # Por ahora null
        
        # Determinar si tiene recordatorio (simple flag en tasks)
        if task.reminders and task.due_date:
            task_data["has_reminder"] = True
        
        # Convertir datetime a string ISO para serialización JSON
        if "due_date" in task_data and task_data["due_date"]:
            task_data["due_date"] = task_data["due_date"].isoformat()

        # Insertar en Supabase
        response = supabase.table("tasks").insert(task_data).execute()
        
        if not response.data:
            raise HTTPException(status_code=500, detail="No se pudo crear la tarea.")
            
        created_task = response.data[0]
        
        # Procesar recordatorios
        reminders_response_data = []
        if task.reminders and task.due_date:
            reminders_to_insert = []
            for rem_config in task.reminders:
                remind_at = calculate_remind_at(task.due_date, rem_config)
                reminders_to_insert.append({
                    "user_id": user_id,
                    "task_id": task_id,
                    "remind_at": remind_at.isoformat(),
                    "status": "pending"
                })
            
            if reminders_to_insert:
                rem_res = supabase.table("reminders").insert(reminders_to_insert).execute()
                if rem_res.data:
                    reminders_response_data = rem_res.data

        created_task["reminders_data"] = reminders_response_data
        
        return created_task

    except Exception as e:
        logger.error(f"Error creando tarea: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=PaginatedTaskResponse, summary="Listar todas las tareas del usuario")
async def list_tasks(
    user=Depends(get_current_user),
    view: Optional[str] = Query(None, pattern="^(home|tasks)$", description="Vista de filtrado inteligente: home (pendientes próximos 7 días), tasks (pendientes sin límite de fecha)"),
    is_completed: Optional[bool] = Query(None, description="Filtrar por estado de completado (ignorado si se usa view)"),
    tag_ids: Optional[List[str]] = Query(None, description="Filtrar por etiquetas (AND: la tarea debe tener TODAS las etiquetas seleccionadas)"),
    priority: Optional[str] = Query(None, pattern="^(baja|media|alta)$", description="Filtrar por prioridad (baja, media, alta)"),
    start_date: Optional[datetime] = Query(None, description="Filtrar desde esta fecha (incluye)"),
    end_date: Optional[datetime] = Query(None, description="Filtrar hasta esta fecha (incluye)"),
    date_field: str = Query("due_date", pattern="^(due_date|updated_at|created_at)$", description="Campo de fecha a usar para el rango"),
    sort_by: str = Query("updated_at", pattern="^(updated_at|due_date|priority)$", description="Ordenar por campo (ignorado si se usa view o cursor)"),
    order: str = Query("desc", pattern="^(asc|desc)$", description="Dirección del ordenamiento (ignorado si se usa view o cursor)"),
    limit: int = Query(10, ge=1, le=50, description="Número de resultados por página (máximo 50)"),
    cursor: Optional[str] = Query(None, description="Cursor de paginación: valor de due_date del último resultado recibido (ISO 8601)"),
):
    """
    Obtiene tareas del usuario autenticado con filtrado, ordenamiento y paginación por cursor.

    **Modos de uso:**
    - `view=home`: tareas pendientes atrasadas + próximos 7 días (sin due_date excluidas).
    - `view=tasks`: tareas pendientes sin límite de fecha (sin due_date al final).
    - Sin `view`: comportamiento clásico con filtros manuales.

    Cuando se usa `view` o `cursor`, el ordenamiento es siempre `due_date ASC`.
    """
    try:
        user_id = user.id

        select_query = "*, reminders(*), task_tags(tags(*)), task_notes(notes(id, title)), event_tasks(events(id, title, start_time))"
        if tag_ids:
            select_query = "*, reminders(*), task_tags!inner(tags(*)), task_notes(notes(id, title)), event_tasks(events(id, title, start_time))"

        query = supabase.table("tasks").select(select_query).eq("user_id", user_id)

        # --- Bloque 1: filtrado por vista ---
        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        max_date = None

        if view == "home":
            max_date = today + timedelta(days=7)
            query = query.lte("due_date", max_date.isoformat())
        elif view is None:
            if is_completed is not None:
                query = query.eq("is_completed", is_completed)

        # Filtros adicionales
        if priority:
            query = query.eq("priority", priority)

        if tag_ids:
            query = query.in_("task_tags.tag_id", tag_ids)

        if start_date:
            query = query.gte(date_field, start_date.isoformat())
        if end_date:
            query = query.lte(date_field, end_date.isoformat())

        # --- Bloque 2: cursor pagination ---
        use_cursor_sort = view is not None or cursor is not None

        if cursor:
            query = query.gt("due_date", cursor)

        if use_cursor_sort:
            query = query.order("due_date", desc=False)
        else:
            is_desc = (order == "desc")
            if sort_by == "due_date":
                query = query.order("due_date", desc=is_desc)
            elif sort_by == "priority":
                query = query.order("priority", desc=is_desc)
            else:
                query = query.order("updated_at", desc=is_desc)

        query = query.limit(limit + 1)
        response = query.execute()
        tasks_raw = response.data

        has_more = len(tasks_raw) > limit
        tasks_raw = tasks_raw[:limit]

        # Post-procesamiento de relaciones
        final_tasks = []
        pending_tasks = []
        completed_tasks = []
        no_due_pending_tasks = []
        required_tag_ids = set(tag_ids) if tag_ids else set()

        for task in tasks_raw:
            if view in ("home", "tasks"):
                due_date_str = task.get("due_date")
                if not due_date_str:
                    if view == "home":
                        continue
                    if view == "tasks":
                        if not task.get("is_completed"):
                            no_due_pending_tasks.append(task)
                        continue
                try:
                    due_dt = datetime.fromisoformat(due_date_str.replace("Z", "+00:00"))
                except ValueError:
                    continue

                if view == "home":
                    if max_date is not None and due_dt > max_date:
                        continue
                    if due_dt < today and task.get("is_completed"):
                        continue
                elif view == "tasks":
                    if due_dt < today and task.get("is_completed"):
                        continue

            tags_list = []
            found_tag_ids = set()

            if "task_tags" in task:
                for item in task["task_tags"]:
                    if item.get("tags"):
                        tag_data = item["tags"]
                        tags_list.append(tag_data)
                        found_tag_ids.add(str(tag_data.get("id")))
            task["tags"] = tags_list
            del task["task_tags"]

            if "reminders" in task:
                task["reminders_data"] = task["reminders"]
                del task["reminders"]
            else:
                task["reminders_data"] = []

            notes_list = []
            if "task_notes" in task:
                for item in task["task_notes"]:
                    if item.get("notes"):
                        notes_list.append(item["notes"])
                del task["task_notes"]
            task["notes"] = notes_list

            events_list = []
            if "event_tasks" in task:
                for item in task["event_tasks"]:
                    if item.get("events"):
                        events_list.append(item["events"])
                del task["event_tasks"]
            task["events"] = events_list

            if tag_ids and not required_tag_ids.issubset(found_tag_ids):
                continue

            if view == "home":
                if task.get("is_completed"):
                    completed_tasks.append(task)
                else:
                    pending_tasks.append(task)
            else:
                final_tasks.append(task)

        if view == "home":
            final_tasks = pending_tasks + completed_tasks
        elif view == "tasks":
            final_tasks = final_tasks + no_due_pending_tasks

        next_cursor = None
        if has_more and final_tasks:
            last_due_date = final_tasks[-1].get("due_date")
            if last_due_date:
                next_cursor = last_due_date

        return PaginatedTaskResponse(data=final_tasks, next_cursor=next_cursor, has_more=has_more)

    except Exception as e:
        logger.error(f"Error listando tareas: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{task_id}", response_model=TaskResponse, summary="Obtener una tarea específica")
async def get_task(task_id: str, user=Depends(get_current_user)):
    """
    Obtiene los detalles de una tarea específica por su ID, incluyendo sus etiquetas y recordatorios.
    """
    try:
        user_id = user.id
        response = supabase.table("tasks").select("*, reminders(*), task_tags(tags(*)), task_notes(notes(id, title, content)), event_tasks(events(id, title, start_time))").eq("id", task_id).eq("user_id", user_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Tarea no encontrada")
            
        task = response.data[0]
        
        # Procesar tags
        tags_list = []
        if "task_tags" in task:
            for item in task["task_tags"]:
                if item.get("tags"):
                    tags_list.append(item["tags"])
        task["tags"] = tags_list
        if "task_tags" in task:
            del task["task_tags"]
            
        # Process linked notes
        notes_list = []
        if "task_notes" in task:
            for item in task["task_notes"]:
                if item.get("notes"):
                    notes_list.append(item["notes"])
            del task["task_notes"]
        task["notes"] = notes_list

        # Process linked events
        events_list = []
        if "event_tasks" in task:
            for item in task["event_tasks"]:
                if item.get("events"):
                    events_list.append(item["events"])
            del task["event_tasks"]
        task["events"] = events_list

        # Mapear recordatorios (ya vienen en el join)
        if "reminders" in task:
            task["reminders_data"] = task["reminders"]
            del task["reminders"]
        else:
            task["reminders_data"] = []

        return task
    except Exception as e:
        logger.error(f"Error obteniendo tarea: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{task_id}/related", response_model=TaskRelatedResponse, summary="Obtener notas y eventos vinculados a una tarea")
async def get_task_related(task_id: str, user=Depends(get_current_user)):
    """
    Retorna solo las notas y eventos vinculados a una tarea, sin recargar el detalle completo.
    Útil para sincronizar el estado local después de un optimistic update fallido en vínculos.
    """
    try:
        user_id = user.id

        task_check = supabase.table("tasks").select("id").eq("id", task_id).eq("user_id", user_id).execute()
        if not task_check.data:
            raise HTTPException(status_code=404, detail="Tarea no encontrada")

        notes_res = supabase.table("task_notes").select("notes(id, title, content)").eq("task_id", task_id).execute()
        notes_list = [item["notes"] for item in (notes_res.data or []) if item.get("notes")]

        events_res = supabase.table("event_tasks").select("events(id, title, start_time)").eq("task_id", task_id).execute()
        events_list = [item["events"] for item in (events_res.data or []) if item.get("events")]

        return TaskRelatedResponse(notes=notes_list, events=events_list)

    except Exception as e:
        logger.error(f"Error obteniendo relaciones de tarea: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.patch("/{task_id}", response_model=TaskResponse, summary="Actualizar una tarea")
async def update_task(task_id: str, task_update: TaskUpdate, user=Depends(get_current_user)):
    """
    Actualiza los campos de una tarea existente.
    Si se actualiza 'due_date' o 'reminders', se recalculan los recordatorios.
    Si 'reminders' es una lista (aunque sea vacía), se reemplazan los recordatorios existentes.
    """
    try:
        user_id = user.id
        
        # Filtrar campos que no son None
        # Excluimos reminders de update_data porque no es columna de tasks
        update_data = {k: v for k, v in task_update.dict(exclude={"reminders"}).items() if v is not None}
        
        # Obtenemos la tarea actual para saber su due_date si no se envía en el update
        current_task_res = supabase.table("tasks").select("due_date, has_reminder").eq("id", task_id).eq("user_id", user_id).execute()
        if not current_task_res.data:
            raise HTTPException(status_code=404, detail="Tarea no encontrada")
        current_task = current_task_res.data[0]
        
        # Determinar nuevo due_date
        new_due_date_str = None
        if "due_date" in update_data and update_data["due_date"]:
             new_due_date_str = update_data["due_date"].isoformat()
             # Actualizamos en el dict para la DB
             update_data["due_date"] = new_due_date_str
        elif current_task.get("due_date"):
             new_due_date_str = current_task.get("due_date")
             
        # Lógica de recordatorios:
        # Si se envían recordatorios explícitamente (lista vacía o con elementos)
        if task_update.reminders is not None:
            # 1. Borrar recordatorios existentes
            supabase.table("reminders").delete().eq("task_id", task_id).execute()
            
            # 2. Si hay nuevos recordatorios y tenemos fecha límite, insertarlos
            if task_update.reminders and new_due_date_str:
                due_date_obj = datetime.fromisoformat(new_due_date_str.replace("Z", "+00:00"))
                reminders_to_insert = []
                for rem_config in task_update.reminders:
                    remind_at = calculate_remind_at(due_date_obj, rem_config)
                    reminders_to_insert.append({
                        "user_id": user_id,
                        "task_id": task_id,
                        "remind_at": remind_at.isoformat(),
                        "status": "pending"
                    })
                supabase.table("reminders").insert(reminders_to_insert).execute()
                update_data["has_reminder"] = True
            else:
                update_data["has_reminder"] = False

        # Si NO se enviaron reminders pero SI cambió la due_date, ¿deberíamos recalcular?
        # Por simplicidad y seguridad: si cambias la fecha y no mandas recordatorios, 
        # asumimos que los recordatorios antiguos quedan inválidos o mal. 
        # Opción A: Borrarlos. Opción B: Intentar ajustarlos (complejo).
        # Decisión: Si cambia fecha y no se especifica reminders, mantenemos los viejos (quizás desfasados) 
        # o el cliente debe enviar siempre reminders si cambia fecha.
        # Asumiremos que el cliente envía todo junto.
        
        if not update_data and task_update.reminders is None:
             raise HTTPException(status_code=400, detail="No se proporcionaron datos para actualizar")

        if update_data:
            update_data["updated_at"] = datetime.now().isoformat()
            response = supabase.table("tasks").update(update_data).eq("id", task_id).eq("user_id", user_id).execute()
        else:
            # Si solo se actualizaron recordatorios, recuperamos la tarea actualizada
            response = supabase.table("tasks").select("*").eq("id", task_id).execute()

        if not response.data:
             raise HTTPException(status_code=404, detail="Tarea no encontrada o no tienes permiso para editarla")
             
        updated_task = response.data[0]
        
        # Recuperar recordatorios actuales para devolver
        reminders_res = supabase.table("reminders").select("*").eq("task_id", task_id).execute()
        updated_task["reminders_data"] = reminders_res.data if reminders_res.data else []
        
        return updated_task
        
    except Exception as e:
        logger.error(f"Error actualizando tarea: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Eliminar una tarea")
async def delete_task(task_id: str, user=Depends(get_current_user)):
    """
    Elimina una tarea permanentemente.
    """
    try:
        user_id = user.id
        
        response = supabase.table("tasks").delete().eq("id", task_id).eq("user_id", user_id).execute()
        
        if not response.data:
             raise HTTPException(status_code=404, detail="Tarea no encontrada o no tienes permiso para eliminarla")
             
        return None 
        
    except Exception as e:
        logger.error(f"Error eliminando tarea: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/tags", status_code=status.HTTP_200_OK, summary="Asignar etiquetas a una tarea")
async def assign_tags_to_task(assignment: TaskAssignTags, user=Depends(get_current_user)):
    """
    Asigna una o más etiquetas a una tarea existente.
    Recibe el ID de la tarea y una lista de IDs de etiquetas.
    """
    try:
        user_id = user.id
        task_id = assignment.task_id
        tag_ids = assignment.tag_ids

        # 1. Verificar que la tarea pertenece al usuario
        task_check = supabase.table("tasks").select("id").eq("id", task_id).eq("user_id", user_id).execute()
        if not task_check.data:
            raise HTTPException(status_code=404, detail="Tarea no encontrada o no te pertenece")

        # 2. Verificar que las etiquetas pertenecen al usuario (opcional pero recomendado)
        # Podríamos hacer un count, pero por simplicidad asumimos que si el cliente manda IDs, son válidos.
        # Si una etiqueta no existe, la inserción fallará por FK si la BD está bien configurada.
        # Pero para mejor UX, intentamos insertar y capturamos error.

        if not tag_ids:
            return {"message": "No se proporcionaron etiquetas para asignar"}

        # 3. Preparar datos para inserción en task_tags
        # Nota: Si ya existe la relación, insert fallará si no usamos upsert o ignore.
        # Supabase-py insert soporta upsert=True? No directamente en insert, sino en upsert().
        # Pero task_tags es tabla pivote.
        # Estrategia: Insertar ignorando duplicados si es posible, o manejar error.
        # O simplemente intentar insertar uno por uno? No, batch es mejor.
        
        data_to_insert = [{"task_id": task_id, "tag_id": tag_id} for tag_id in tag_ids]
        
        # Usamos upsert para evitar errores de duplicados (on_conflict en task_id, tag_id)
        # upsert requiere que la tabla tenga restricción unique en esas columnas (que es la PK).
        response = supabase.table("task_tags").upsert(data_to_insert, on_conflict="task_id, tag_id", ignore_duplicates=True).execute()

        if hasattr(response, 'error') and response.error:
             raise Exception(response.error.message)

        return {"message": "Etiquetas asignadas correctamente", "assigned_count": len(tag_ids)}

    except Exception as e:
        logger.error(f"Error asignando etiquetas: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/notes", status_code=status.HTTP_201_CREATED, summary="Vincular nota a tarea")
async def link_note_to_task(link: TaskLinkNote, user=Depends(get_current_user)):
    """
    Crea una relación entre una tarea y una nota. Ambas deben pertenecer al usuario.
    """
    try:
        user_id = user.id
        
        # 1. Verificar propiedad de tarea
        task_check = supabase.table("tasks").select("id").eq("id", link.task_id).eq("user_id", user_id).execute()
        if not task_check.data:
            raise HTTPException(status_code=404, detail="Tarea no encontrada")

        # 2. Verificar propiedad de nota
        note_check = supabase.table("notes").select("id").eq("id", link.note_id).eq("user_id", user_id).execute()
        if not note_check.data:
            raise HTTPException(status_code=404, detail="Nota no encontrada")
            
        # 3. Insertar relación
        # Usamos upsert o ignore por si ya existe
        response = supabase.table("task_notes").upsert({
            "task_id": link.task_id,
            "note_id": link.note_id
        }, on_conflict="task_id, note_id", ignore_duplicates=True).execute()
        
        return {"message": "Nota vinculada a la tarea exitosamente"}
        
    except Exception as e:
        logger.error(f"Error vinculando nota a tarea: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{task_id}/notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Desvincular nota de tarea")
async def unlink_note_from_task(task_id: str, note_id: str, user=Depends(get_current_user)):
    """
    Elimina la relación entre una tarea y una nota.
    """
    try:
        user_id = user.id
        
        # Verificar propiedad de tarea (la política RLS lo haría, pero validamos para 404)
        task_check = supabase.table("tasks").select("id").eq("id", task_id).eq("user_id", user_id).execute()
        if not task_check.data:
             raise HTTPException(status_code=404, detail="Tarea no encontrada")

        response = supabase.table("task_notes").delete().eq("task_id", task_id).eq("note_id", note_id).execute()
        
        return None
    except Exception as e:
         logger.error(f"Error desvinculando nota: {e}")
         raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{task_id}/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Desvincular etiqueta de tarea")
async def remove_tag_from_task(task_id: str, tag_id: str, user=Depends(get_current_user)):
    """
    Elimina la asociación entre una tarea y una etiqueta.
    """
    try:
        user_id = user.id

        # 1. Verificar que la tarea pertenece al usuario
        task_check = supabase.table("tasks").select("id").eq("id", task_id).eq("user_id", user_id).execute()
        if not task_check.data:
            raise HTTPException(status_code=404, detail="Tarea no encontrada o no te pertenece")

        # 2. Eliminar la relación en task_tags
        response = supabase.table("task_tags").delete().eq("task_id", task_id).eq("tag_id", tag_id).execute()

        return None

    except Exception as e:
        logger.error(f"Error desvinculando etiqueta: {e}")
        raise HTTPException(status_code=400, detail=str(e))
