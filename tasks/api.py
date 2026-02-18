from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional
import uuid
from datetime import datetime, timedelta

try:
    from backend.database import supabase
    from backend.tasks.schemas import TaskCreate, TaskUpdate, TaskResponse, TaskAssignTags, ReminderConfig, TaskLinkNote
    from backend.auth.dependencies import get_current_user
except ImportError:
    from database import supabase
    from tasks.schemas import TaskCreate, TaskUpdate, TaskResponse, TaskAssignTags, ReminderConfig, TaskLinkNote
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

@router.get("/", response_model=List[TaskResponse], summary="Listar todas las tareas del usuario")
async def list_tasks(
    user=Depends(get_current_user),
    is_completed: Optional[bool] = Query(None, description="Filtrar por estado de completado"),
    tag_ids: Optional[List[str]] = Query(None, description="Filtrar por etiquetas (AND: la tarea debe tener TODAS las etiquetas seleccionadas)"),
    priority: Optional[str] = Query(None, pattern="^(baja|media|alta)$", description="Filtrar por prioridad (baja, media, alta)"),
    start_date: Optional[datetime] = Query(None, description="Filtrar desde esta fecha (incluye)"),
    end_date: Optional[datetime] = Query(None, description="Filtrar hasta esta fecha (incluye)"),
    date_field: str = Query("due_date", pattern="^(due_date|updated_at|created_at)$", description="Campo de fecha a usar para el rango"),
    sort_by: str = Query("updated_at", pattern="^(updated_at|due_date|priority)$", description="Ordenar por fecha o prioridad"),
    order: str = Query("desc", pattern="^(asc|desc)$", description="Dirección del ordenamiento")
):
    """
    Obtiene todas las tareas del usuario autenticado, con opciones de filtrado y ordenamiento.
    Si se proporcionan múltiples etiquetas, se filtran las tareas que contengan TODAS ellas.
    """
    try:
        user_id = user.id
        
        # Construir la query base
        # Si filtramos por tags, necesitamos usar inner join (!inner) en task_tags para filtrar las tareas iniciales (candidatas)
        # En el listado solo necesitamos título de la nota, no el contenido completo
        select_query = "*, reminders(*), task_tags(tags(*)), task_notes(notes(id, title)), event_tasks(events(id, title, start_time))"
        if tag_ids:
            select_query = "*, reminders(*), task_tags!inner(tags(*)), task_notes(notes(id, title)), event_tasks(events(id, title, start_time))"
            
        query = supabase.table("tasks").select(select_query).eq("user_id", user_id)
        
        # Filtros
        if is_completed is not None:
            query = query.eq("is_completed", is_completed)

        if priority:
            query = query.eq("priority", priority)
            
        if tag_ids:
            # Primero filtramos tareas que tengan AL MENOS UNO de los tags (OR a nivel de DB)
            query = query.in_("task_tags.tag_id", tag_ids)
        
        # Filtro por rango de fechas en el campo indicado
        if start_date:
            query = query.gte(date_field, start_date.isoformat())
        if end_date:
            query = query.lte(date_field, end_date.isoformat())
            
        # Ordenamiento
        is_desc = (order == "desc")
        
        if sort_by == "due_date":
            query = query.order("due_date", desc=is_desc)
        elif sort_by == "priority":
            # Ordenar por prioridad es tricky porque es texto. 
            # Idealmente mapearíamos a int en DB, pero Supabase/Postgres ordena texto alfabéticamente.
            # alta < baja < media (alfabético). No es ideal.
            # Para MVP ordenamos alfabéticamente, o el frontend ordena.
            # Si queremos orden semántico (Alta > Media > Baja), requeriría una función o columna calculada.
            # Por ahora ordenamos por la columna texto.
            query = query.order("priority", desc=is_desc)
        else:
            query = query.order("updated_at", desc=is_desc)
            
        response = query.execute()
        
        tasks = response.data
        
        # Procesar y filtrar (AND logic)
        final_tasks = []
        required_tag_ids = set(tag_ids) if tag_ids else set()

        for task in tasks:
            tags_list = []
            found_tag_ids = set()
            
            if "task_tags" in task:
                for item in task["task_tags"]:
                    if item.get("tags"):
                        tag_data = item["tags"]
                        tags_list.append(tag_data)
                        found_tag_ids.add(str(tag_data.get("id")))

            task["tags"] = tags_list
            # Eliminamos la clave temporal del join
            if "task_tags" in task:
                del task["task_tags"]
            
            # Mapear reminders
            if "reminders" in task:
                task["reminders_data"] = task["reminders"]
                del task["reminders"]
            else:
                task["reminders_data"] = []

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
            
            # Aplicar filtro AND estricto
            if tag_ids:
                # Solo incluimos la tarea si tiene TODOS los tags solicitados
                if required_tag_ids.issubset(found_tag_ids):
                    final_tasks.append(task)
            else:
                final_tasks.append(task)

        return final_tasks
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
