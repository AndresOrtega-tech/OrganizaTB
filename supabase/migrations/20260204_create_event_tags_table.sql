-- Tabla intermedia para relación N:M entre Eventos y Etiquetas (Tags)
CREATE TABLE public.event_tags (
    event_id UUID REFERENCES public.events(id) ON DELETE CASCADE,
    tag_id UUID REFERENCES public.tags(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (event_id, tag_id)
);

-- RLS
ALTER TABLE public.event_tags ENABLE ROW LEVEL SECURITY;

-- Política de seguridad:
-- Permitir acceso si el usuario es dueño del evento
CREATE POLICY "EventTags Policy" ON public.event_tags FOR ALL USING (
    EXISTS (SELECT 1 FROM public.events WHERE id = event_tags.event_id AND user_id = auth.uid())
) WITH CHECK (
    EXISTS (SELECT 1 FROM public.events WHERE id = event_tags.event_id AND user_id = auth.uid())
);
