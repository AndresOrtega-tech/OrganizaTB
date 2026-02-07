UPDATE public.notes SET content = LEFT(content, 800) WHERE char_length(content) > 800;

ALTER TABLE public.notes ADD CONSTRAINT notes_content_length_check CHECK (char_length(content) <= 800);
