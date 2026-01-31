from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional
import uuid
from datetime import datetime
try:
    from backend.database import supabase
    from backend.tasks.schemas import TaskCreate, TaskUpdate, TaskResponse, TaskAssignTags
    from backend.auth.dependencies import get_current_user
except ImportError:
    from database import supabase
    from tasks.schemas import TaskCreate, TaskUpdate, TaskResponse, TaskAssignTags
    from auth.dependencies import get_current_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED, summary="Crear una nueva tarea")
async def create_task(task: TaskCreate, user=Depends(get_current_user)):
    """
    Crea una nueva tarea para el usuario autenticado.
    El ID de la tarea se genera automáticamente y se asigna también como calendar_event_id.
    """
    try:
        user_id = user.id
        
        # Generar UUID explícitamente para asignarlo a calendar_event_id
        task_id = str(uuid.uuid4())
        
        task_data = task.dict()
        task_data["id"] = task_id
        task_data["user_id"] = user_id
        task_data["calendar_event_id"] = task_id # Mismo que el ID
        task_data["media_url"] = None # Por ahora null
        
        # Convertir datetime a string ISO para serialización JSON
        if "due_date" in task_data and task_data["due_date"]:
            task_data["due_date"] = task_data["due_date"].isoformat()

        # Insertar en Supabase
        response = supabase.table("tasks").insert(task_data).execute()
        
        if not response.data:
            raise HTTPException(status_code=500, detail="No se pudo crear la tarea.")
            
        return response.data[0]

    except Exception as e:
        logger.error(f"Error creando tarea: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=List[TaskResponse], summary="Listar todas las tareas del usuario")
async def list_tasks(
    user=Depends(get_current_user),
    is_completed: Optional[bool] = Query(None, description="Filtrar por estado de completado"),
    tag_ids: Optional[List[str]] = Query(None, description="Filtrar por etiquetas (AND: la tarea debe tener TODAS las etiquetas seleccionadas)"),
    sort_by: str = Query("updated_at", pattern="^(updated_at|due_date)$", description="Ordenar por fecha de actualización o vencimiento"),
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
        select_query = "*, task_tags(tags(*))"
        if tag_ids:
            select_query = "*, task_tags!inner(tags(*))"
            
        query = supabase.table("tasks").select(select_query).eq("user_id", user_id)
        
        # Filtros
        if is_completed is not None:
            query = query.eq("is_completed", is_completed)
            
        if tag_ids:
            # Primero filtramos tareas que tengan AL MENOS UNO de los tags (OR a nivel de DB)
            query = query.in_("task_tags.tag_id", tag_ids)
            
        # Ordenamiento
        is_desc = (order == "desc")
        
        if sort_by == "due_date":
            query = query.order("due_date", desc=is_desc)
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
    Obtiene los detalles de una tarea específica por su ID, incluyendo sus etiquetas.
    """
    try:
        user_id = user.id
        response = supabase.table("tasks").select("*, task_tags(tags(*))").eq("id", task_id).eq("user_id", user_id).execute()
        
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
            
        return task
    except Exception as e:
        logger.error(f"Error obteniendo tarea: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.patch("/{task_id}", response_model=TaskResponse, summary="Actualizar una tarea")
async def update_task(task_id: str, task_update: TaskUpdate, user=Depends(get_current_user)):
    """
    Actualiza los campos de una tarea existente.
    """
    try:
        user_id = user.id
        
        # Filtrar campos que no son None
        update_data = {k: v for k, v in task_update.dict().items() if v is not None}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No se proporcionaron datos para actualizar")
            
        # Convertir datetime a string ISO si es necesario
        if "due_date" in update_data and update_data["due_date"]:
            update_data["due_date"] = update_data["due_date"].isoformat()

        update_data["updated_at"] = datetime.now().isoformat()

        response = supabase.table("tasks").update(update_data).eq("id", task_id).eq("user_id", user_id).execute()
        
        if not response.data:
             raise HTTPException(status_code=404, detail="Tarea no encontrada o no tienes permiso para editarla")
             
        return response.data[0]
        
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
