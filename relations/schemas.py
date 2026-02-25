from pydantic import BaseModel, Field


class TaskNoteLink(BaseModel):
    task_id: str = Field(..., description="ID of the task")
    note_id: str = Field(..., description="ID of the note")


class TaskEventLink(BaseModel):
    task_id: str = Field(..., description="ID of the task")
    event_id: str = Field(..., description="ID of the event")


class NoteEventLink(BaseModel):
    note_id: str = Field(..., description="ID of the note")
    event_id: str = Field(..., description="ID of the event")

