-- 1. Tabla de Eventos
CREATE TABLE public.events (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES auth.users ON DELETE CASCADE NOT NULL,
    title TEXT NOT NULL,
    description TEXT CHECK (char_length(description) <= 500),
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE NOT NULL,
    location TEXT,
    is_all_day BOOLEAN DEFAULT FALSE,
    has_reminder BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Actualizar tabla reminders para soportar eventos (polimorfismo simple o columna nullable)
-- Agregamos columna event_id
ALTER TABLE public.reminders ADD COLUMN event_id UUID REFERENCES public.events(id) ON DELETE CASCADE;

-- Modificar constraint: task_id o event_id debe estar presente (pero task_id era NOT NULL antes)
-- Primero hacemos task_id nullable
ALTER TABLE public.reminders ALTER COLUMN task_id DROP NOT NULL;

-- Agregar constraint CHECK
ALTER TABLE public.reminders ADD CONSTRAINT reminders_source_check 
    CHECK (
        (task_id IS NOT NULL AND event_id IS NULL) OR 
        (task_id IS NULL AND event_id IS NOT NULL)
    );

-- 3. Tabla intermedia Eventos-Tareas
CREATE TABLE public.event_tasks (
    event_id UUID REFERENCES public.events(id) ON DELETE CASCADE,
    task_id UUID REFERENCES public.tasks(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (event_id, task_id)
);

-- 4. Tabla intermedia Eventos-Notas
CREATE TABLE public.event_notes (
    event_id UUID REFERENCES public.events(id) ON DELETE CASCADE,
    note_id UUID REFERENCES public.notes(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (event_id, note_id)
);

-- 5. RLS
ALTER TABLE public.events ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.event_tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.event_notes ENABLE ROW LEVEL SECURITY;

-- Políticas Events
CREATE POLICY "Events Select" ON public.events FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Events Update" ON public.events FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Events Delete" ON public.events FOR DELETE USING (auth.uid() = user_id);
CREATE POLICY "Events Insert" ON public.events FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Políticas Event Tasks
CREATE POLICY "EventTasks Policy" ON public.event_tasks FOR ALL USING (
    EXISTS (SELECT 1 FROM public.events WHERE id = event_tasks.event_id AND user_id = auth.uid())
) WITH CHECK (
    EXISTS (SELECT 1 FROM public.events WHERE id = event_tasks.event_id AND user_id = auth.uid())
);

-- Políticas Event Notes
CREATE POLICY "EventNotes Policy" ON public.event_notes FOR ALL USING (
    EXISTS (SELECT 1 FROM public.events WHERE id = event_notes.event_id AND user_id = auth.uid())
) WITH CHECK (
    EXISTS (SELECT 1 FROM public.events WHERE id = event_notes.event_id AND user_id = auth.uid())
);
