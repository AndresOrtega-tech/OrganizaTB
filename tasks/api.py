from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional
import uuid
from datetime import datetime, timedelta, timezone

try:
    from backend.database import supabase
    from backend.tasks.schemas import (
        TaskCreate,
        TaskUpdate,
        TaskResponse,
        TaskCreateResponse,
        TaskAssignTags,
        ReminderConfig,
        TaskRelatedResponse,
        PaginatedTaskResponse,
    )
    from backend.auth.dependencies import get_current_user
except ImportError:
    from database import supabase
    from tasks.schemas import (
        TaskCreate,
        TaskUpdate,
        TaskResponse,
        TaskCreateResponse,
        TaskAssignTags,
        ReminderConfig,
        TaskRelatedResponse,
        PaginatedTaskResponse,
    )
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

@router.post("/", response_model=TaskCreateResponse, status_code=status.HTTP_201_CREATED, summary="Crear una nueva tarea")
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
    view: Optional[str] = Query(None, pattern="^(home|tasks)$", description="Modo de vista: home o tasks"),
    tab: Optional[str] = Query(None, pattern="^(pending|completed)$", description="Tab en view=tasks: pending o completed"),
    tag_ids: Optional[List[str]] = Query(None, description="Filtrar por etiquetas (AND: la tarea debe tener TODAS las etiquetas seleccionadas)"),
    priority: Optional[str] = Query(None, pattern="^(baja|media|alta)$", description="Filtrar por prioridad (baja, media, alta)"),
    end_date: Optional[datetime] = Query(None, description="Filtrar tareas con due_date hasta esta fecha"),
    limit: int = Query(10, ge=1, le=50, description="Límite de tareas por página"),
    cursor: Optional[datetime] = Query(None, description="Cursor de paginación basado en due_date del último resultado")
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
        now = datetime.utcnow()
        today = now.date()

        effective_view = view or "tasks"

        def map_reminders(task: dict) -> None:
            if "reminders" in task:
                task["reminders_data"] = task["reminders"]
                del task["reminders"]
            else:
                task["reminders_data"] = []

        def extract_tags(task: dict) -> None:
            # Extrae tags del join task_tags y las pone en task["tags"]
            tags_list = []
            if "task_tags" in task:
                for item in task["task_tags"]:
                    if item.get("tags"):
                        tags_list.append(item["tags"])
                del task["task_tags"]
            task["tags"] = tags_list

        if effective_view == "home":
            # Ignorar filtros manipulables y limitar el conjunto en BD a la ventana relevante
            today_iso = today.isoformat()
            window_end = today + timedelta(days=7)
            window_end_iso = window_end.isoformat()

            # Tareas pendientes atrasadas (is_completed=false, due_date < hoy)
            # y tareas (pendientes y completadas) dentro de hoy..hoy+7
            or_condition = (
                f"and(is_completed.eq.false,due_date.lt.{today_iso}),"
                f"and(due_date.gte.{today_iso},due_date.lte.{window_end_iso})"
            )

            response = (
                supabase
                .table("tasks")
                .select("*, reminders(*), task_tags(tags(id, name, color, icon))")
                .eq("user_id", user_id)
                .or_(or_condition)
                .execute()
            )
            tasks = response.data or []

            tasks_with_due_date = []
            for task in tasks:
                due = task.get("due_date")
                if not due:
                    continue
                try:
                    due_dt = datetime.fromisoformat(str(due).replace("Z", "+00:00"))
                except Exception:
                    continue
                task["_due_dt"] = due_dt
                tasks_with_due_date.append(task)

            overdue_pending = []
            future_pending = []
            future_completed = []

            for task in tasks_with_due_date:
                due_dt = task["_due_dt"]
                due_date = due_dt.date()
                is_completed = bool(task.get("is_completed"))

                if not is_completed and due_date < today:
                    overdue_pending.append(task)
                elif today <= due_date <= window_end:
                    if not is_completed:
                        future_pending.append(task)
                    else:
                        future_completed.append(task)

            overdue_pending.sort(key=lambda t: t["_due_dt"])
            future_pending.sort(key=lambda t: t["_due_dt"])
            future_completed.sort(key=lambda t: t["_due_dt"])

            ordered = overdue_pending + future_pending + future_completed

            if cursor:
                ordered = [t for t in ordered if t.get("_due_dt") and t["_due_dt"] > cursor]

            page = ordered[:limit]
            has_more = len(ordered) > limit
            next_cursor = None
            if page and has_more:
                last_due_dt = page[-1].get("_due_dt")
                if last_due_dt:
                    next_cursor = last_due_dt

            for task in page:
                map_reminders(task)
                extract_tags(task)
                if "_due_dt" in task:
                    del task["_due_dt"]

            return {
                "data": page,
                "next_cursor": next_cursor,
                "has_more": has_more,
            }

        # view=tasks (o modo por defecto)
        effective_tab = tab or "pending"

        # Siempre traemos tags; si hay filtro por tag_ids usamos !inner para filtrar
        if tag_ids:
            select_query = "*, reminders(*), task_tags!inner(tags(id, name, color, icon))"
        else:
            select_query = "*, reminders(*), task_tags(tags(id, name, color, icon))"

        query = supabase.table("tasks").select(select_query).eq("user_id", user_id)

        if effective_tab == "pending":
            query = query.eq("is_completed", False)
        else:
            query = query.eq("is_completed", True)

        if priority:
            query = query.eq("priority", priority)

        response = query.execute()
        tasks = response.data or []

        required_tag_ids = set(tag_ids) if tag_ids else set()
        filtered = []

        for task in tasks:
            # Extraer tags y aplicar filtro AND si corresponde
            found_tag_ids = set()
            tags_list = []
            if "task_tags" in task:
                for item in task["task_tags"]:
                    if item.get("tags"):
                        tag_data = item["tags"]
                        found_tag_ids.add(str(tag_data.get("id")))
                        tags_list.append(tag_data)
                del task["task_tags"]
            task["tags"] = tags_list

            if tag_ids and not required_tag_ids.issubset(found_tag_ids):
                continue

            due = task.get("due_date")
            due_dt = None
            if due:
                try:
                    due_dt = datetime.fromisoformat(str(due).replace("Z", "+00:00"))
                except Exception:
                    due_dt = None

            if end_date and due_dt and due_dt > end_date:
                continue

            task["_due_dt"] = due_dt
            filtered.append(task)

        dated = [t for t in filtered if t["_due_dt"] is not None]
        no_date = [t for t in filtered if t["_due_dt"] is None]

        if effective_tab == "pending":
            overdue = []
            future = []
            for task in dated:
                due_date = task["_due_dt"].date()
                if due_date < today:
                    overdue.append(task)
                else:
                    future.append(task)

            overdue.sort(key=lambda t: t["_due_dt"])
            future.sort(key=lambda t: t["_due_dt"])
            ordered = overdue + future + no_date
        else:
            dated.sort(key=lambda t: t["_due_dt"], reverse=True)
            ordered = dated + no_date

        for task in ordered:
            map_reminders(task)
            if "_due_dt" in task:
                del task["_due_dt"]

        if cursor:
            if effective_tab == "pending":
                ordered = [t for t in ordered if t.get("due_date") and datetime.fromisoformat(str(t.get("due_date")).replace("Z", "+00:00")) > cursor]
            else:
                ordered = [t for t in ordered if t.get("due_date") and datetime.fromisoformat(str(t.get("due_date")).replace("Z", "+00:00")) < cursor]

        page = ordered[:limit]
        has_more = len(ordered) > limit
        next_cursor = None
        if page and has_more:
            last_due = page[-1].get("due_date")
            if last_due:
                try:
                    next_cursor = datetime.fromisoformat(str(last_due).replace("Z", "+00:00"))
                except Exception:
                    next_cursor = None

        return {
            "data": page,
            "next_cursor": next_cursor,
            "has_more": has_more,
        }
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
        response = supabase.table("tasks").select("*, reminders(*)").eq("id", task_id).eq("user_id", user_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Tarea no encontrada")
            
        task = response.data[0]
        
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

@router.get("/{task_id}/related", response_model=TaskRelatedResponse, summary="Obtener relaciones de una tarea")
async def get_task_related(task_id: str, user=Depends(get_current_user)):
    try:
        user_id = user.id
        response = supabase.table("tasks").select(
            "task_tags(tags(id, name, color, icon)), "
            "task_notes(notes(id, title, content)), "
            "event_tasks(events(id, title, start_time))"
        ).eq("id", task_id).eq("user_id", user_id).execute()

        if not response.data:
            raise HTTPException(status_code=404, detail="Tarea no encontrada")

        task = response.data[0]

        tags_list = []
        if "task_tags" in task:
            for item in task["task_tags"]:
                if item.get("tags"):
                    tags_list.append(item["tags"])

        notes_list = []
        if "task_notes" in task:
            for item in task["task_notes"]:
                if item.get("notes"):
                    notes_list.append(item["notes"])

        events_list = []
        if "event_tasks" in task:
            for item in task["event_tasks"]:
                if item.get("events"):
                    events_list.append(item["events"])

        return {
            "tags": tags_list,
            "notes": notes_list,
            "events": events_list,
        }
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
        
        # Filtrar campos según lo que realmente se envió (exclude_unset)
        # Excluimos reminders de update_data porque no es columna de tasks
        update_data = task_update.dict(exclude={"reminders"}, exclude_unset=True)
        
        # Obtenemos la tarea actual para saber su due_date si no se envía en el update
        current_task_res = supabase.table("tasks").select("due_date, has_reminder").eq("id", task_id).eq("user_id", user_id).execute()
        if not current_task_res.data:
            raise HTTPException(status_code=404, detail="Tarea no encontrada")
        current_task = current_task_res.data[0]
        
        # Determinar nuevo due_date
        new_due_date_str = None
        if "due_date" in update_data:
             if update_data["due_date"] is not None:
                 new_due_date_str = update_data["due_date"].isoformat()
                 # Actualizamos en el dict para la DB
                 update_data["due_date"] = new_due_date_str
             else:
                 # Se envió due_date explícitamente como null -> lo dejamos como None (DB lo pondrá en NULL)
                 new_due_date_str = None
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

@router.post("/{task_id}/tags", status_code=status.HTTP_200_OK, summary="Asignar etiqueta a una tarea")
async def assign_tag_to_task(task_id: str, assignment: TaskAssignTags, user=Depends(get_current_user)):
    """
    Asigna una o más etiquetas a una tarea existente.
    Recibe el ID de la tarea y una lista de IDs de etiquetas.
    """
    try:
        user_id = user.id
        tag_id = assignment.tag_id

        # 1. Verificar que la tarea pertenece al usuario
        task_check = supabase.table("tasks").select("id").eq("id", task_id).eq("user_id", user_id).execute()
        if not task_check.data:
            raise HTTPException(status_code=404, detail="Tarea no encontrada o no te pertenece")

        # 2. Verificar que las etiquetas pertenecen al usuario (opcional pero recomendado)
        # Podríamos hacer un count, pero por simplicidad asumimos que si el cliente manda IDs, son válidos.
        # Si una etiqueta no existe, la inserción fallará por FK si la BD está bien configurada.
        # Pero para mejor UX, intentamos insertar y capturamos error.

        # 2b. Verificar si la relación ya existe (idempotencia)
        exists = supabase.table("task_tags").select("task_id").eq("task_id", task_id).eq("tag_id", tag_id).execute()
        if exists.data:
            return {"message": "Etiqueta asignada correctamente", "assigned": 0}

        # 3. Insertar relación
        response = supabase.table("task_tags").insert({"task_id": task_id, "tag_id": tag_id}).execute()
        if not response.data:
            raise HTTPException(status_code=500, detail="No se pudo asignar la etiqueta")

        return {"message": "Etiqueta asignada correctamente", "assigned": 1}

    except Exception as e:
        logger.error(f"Error asignando etiquetas: {e}")
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
        supabase.table("task_tags").delete().eq("task_id", task_id).eq("tag_id", tag_id).execute()

        return None

    except Exception as e:
        logger.error(f"Error desvinculando etiqueta: {e}")
        raise HTTPException(status_code=400, detail=str(e))
