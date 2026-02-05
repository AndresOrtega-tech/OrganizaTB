UPDATE public.tasks SET description = LEFT(description, 500) WHERE char_length(description) > 500;

ALTER TABLE public.tasks ADD CONSTRAINT tasks_description_length_check CHECK (char_length(description) <= 500);
