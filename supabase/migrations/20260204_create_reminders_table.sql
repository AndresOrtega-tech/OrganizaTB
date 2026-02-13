CREATE TABLE public.reminders (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES auth.users ON DELETE CASCADE NOT NULL,
    task_id UUID REFERENCES public.tasks(id) ON DELETE CASCADE NOT NULL,
    remind_at TIMESTAMP WITH TIME ZONE NOT NULL,
    status TEXT DEFAULT 'pending', -- pending, sent, failed
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- RLS
ALTER TABLE public.reminders ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Reminders Select" ON public.reminders FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Reminders Update" ON public.reminders FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Reminders Delete" ON public.reminders FOR DELETE USING (auth.uid() = user_id);
CREATE POLICY "Reminders Insert" ON public.reminders FOR INSERT WITH CHECK (auth.uid() = user_id);
