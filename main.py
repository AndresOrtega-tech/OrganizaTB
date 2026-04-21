from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import logging

# Configuración de logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from database import supabase
from auth.api import router as auth_router, users_router
from auth.dependencies import get_current_user
from tags.api import router as tags_router
from tasks.api import router as tasks_router
from notes.api import router as notes_router
from events.api import router as events_router
from reminders.api import router as reminders_router
from relations.api import router as relations_router

# Configuración de Rate Limiting
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="OrganizaT API",
    description="API para la gestión de usuarios y tareas de OrganizaT",
    version="1.0.0",
)

# Conectar el limiter a la app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configuración de CORS
origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:8081",
    "https://web-app-organiza-t.vercel.app",
    "https://web-app-organiza-t-git-development-andresortegatechs-projects.vercel.app/"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])
app.include_router(users_router, prefix="/api/users", tags=["Users"])
app.include_router(tags_router, prefix="/api/tags", tags=["Tags"])
app.include_router(tasks_router, prefix="/api/tasks", tags=["Tasks"])
app.include_router(notes_router, prefix="/api/notes", tags=["Notes"])
app.include_router(events_router, prefix="/api/events", tags=["Events"])
app.include_router(reminders_router, prefix="/api/reminders", tags=["Reminders"])
app.include_router(relations_router, prefix="/api/relations", tags=["Relations"])

@app.get("/", tags=["Health"])
def read_root():
    return {"message": "Hola Mundo desde FastAPI en Vercel"}

@app.get("/health", tags=["Health"])
def health_check():
    try:
        return {
            "status": "ok",
            "supabase_connected": True if supabase else False,
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "error"}


@app.get("/tables", tags=["Health"])
def list_tables(user=Depends(get_current_user)):
    if supabase is None:
        return {
            "status": "error",
            "message": "Supabase no está configurado."
        }

    try:
        response = supabase.rpc("get_tables", {}).execute()
        return {"tables": response.data}
    except Exception as e:
        logger.error(f"Error listing tables: {e}")
        return {
            "status": "error",
            "message": "No se pudieron listar las tablas."
        }
