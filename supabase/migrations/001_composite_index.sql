-- Bloque 4: Índice compuesto para queries de GET /api/tasks/
-- Cubre los filtros combinados: user_id + is_completed + due_date
-- Ejecutar en Supabase SQL Editor ANTES de implementar Bloques 1 y 2.

CREATE INDEX IF NOT EXISTS idx_tasks_user_completed_due
ON public.tasks(user_id, is_completed, due_date);
