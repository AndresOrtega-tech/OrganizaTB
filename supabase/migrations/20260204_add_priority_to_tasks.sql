-- Agregar columna priority a la tabla tasks
ALTER TABLE public.tasks ADD COLUMN priority TEXT DEFAULT 'media';

-- Validar que solo acepte valores permitidos (enum simulado)
ALTER TABLE public.tasks ADD CONSTRAINT tasks_priority_check CHECK (priority IN ('baja', 'media', 'alta'));
