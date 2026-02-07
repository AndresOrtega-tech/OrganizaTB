-- Tabla intermedia para relación N:M entre Tareas y Notas
CREATE TABLE public.task_notes (
    task_id UUID REFERENCES public.tasks(id) ON DELETE CASCADE,
    note_id UUID REFERENCES public.notes(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (task_id, note_id)
);

-- RLS
ALTER TABLE public.task_notes ENABLE ROW LEVEL SECURITY;

-- Política de seguridad:
-- Permitir acceso si el usuario es dueño de la tarea O de la nota (deberían ser del mismo dueño)
-- Verificamos la propiedad a través de la tarea asociada
CREATE POLICY "TaskNotes Policy" ON public.task_notes FOR ALL USING (
    EXISTS (SELECT 1 FROM public.tasks WHERE id = task_notes.task_id AND user_id = auth.uid())
) WITH CHECK (
    EXISTS (SELECT 1 FROM public.tasks WHERE id = task_notes.task_id AND user_id = auth.uid())
);
