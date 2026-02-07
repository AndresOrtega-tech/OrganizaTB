-- Agregar constraint para limitar summary a 500 caracteres
UPDATE public.notes SET summary = LEFT(summary, 500) WHERE char_length(summary) > 500;

ALTER TABLE public.notes ADD CONSTRAINT notes_summary_length_check CHECK (char_length(summary) <= 500);
