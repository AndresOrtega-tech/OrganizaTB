from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional
from datetime import datetime
try:
    from backend.database import supabase
    from backend.reminders.schemas import ReminderResponse, ReminderUpdate
    from backend.auth.dependencies import get_current_user
except ImportError:
    from database import supabase
    from reminders.schemas import ReminderResponse, ReminderUpdate
    from auth.dependencies import get_current_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/", response_model=List[ReminderResponse], summary="Listar todos los recordatorios")
async def list_reminders(
    user=Depends(get_current_user),
    status: Optional[str] = Query(None, description="Filtrar por estado (pending, sent, failed)"),
    start_date: Optional[datetime] = Query(None, description="Desde fecha de recordatorio"),
    end_date: Optional[datetime] = Query(None, description="Hasta fecha de recordatorio")
):
    """
    Obtiene todos los recordatorios del usuario, permitiendo filtrar por estado y rango de fechas.
    Incluye información básica de la tarea o evento asociado.
    """
    try:
        user_id = user.id
        
        # Seleccionamos también datos de task y event relacionados
        query = supabase.table("reminders").select(
            "*, tasks(title), events(title)"
        ).eq("user_id", user_id)
        
        if status:
            query = query.eq("status", status)
            
        if start_date:
            query = query.gte("remind_at", start_date.isoformat())
            
        if end_date:
            query = query.lte("remind_at", end_date.isoformat())
            
        # Ordenar por fecha próxima
        query = query.order("remind_at", desc=False)
            
        response = query.execute()
        
        # Mapear respuesta para aplanar títulos
        reminders = []
        for item in response.data:
            rem = item.copy()
            if rem.get("tasks"):
                rem["task_title"] = rem["tasks"].get("title")
            if rem.get("events"):
                rem["event_title"] = rem["events"].get("title")
            
            # Limpiar dicts anidados
            if "tasks" in rem: del rem["tasks"]
            if "events" in rem: del rem["events"]
            
            reminders.append(rem)
            
        return reminders
        
    except Exception as e:
        logger.error(f"Error listando recordatorios: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.patch("/{reminder_id}", response_model=ReminderResponse, summary="Actualizar recordatorio")
async def update_reminder(reminder_id: str, update: ReminderUpdate, user=Depends(get_current_user)):
    """
    Actualiza el estado o fecha de un recordatorio específico.
    """
    try:
        user_id = user.id
        
        update_data = {k: v for k, v in update.dict().items() if v is not None}
        if not update_data:
             raise HTTPException(status_code=400, detail="No hay datos para actualizar")
             
        if "remind_at" in update_data:
            update_data["remind_at"] = update_data["remind_at"].isoformat()

        response = supabase.table("reminders").update(update_data).eq("id", reminder_id).eq("user_id", user_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Recordatorio no encontrado")
            
        return response.data[0]
        
    except Exception as e:
        logger.error(f"Error actualizando recordatorio: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{reminder_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Eliminar recordatorio")
async def delete_reminder(reminder_id: str, user=Depends(get_current_user)):
    try:
        user_id = user.id
        response = supabase.table("reminders").delete().eq("id", reminder_id).eq("user_id", user_id).execute()
        
        if not response.data:
             raise HTTPException(status_code=404, detail="Recordatorio no encontrado")
             
    except Exception as e:
        logger.error(f"Error eliminando recordatorio: {e}")
        raise HTTPException(status_code=400, detail=str(e))
