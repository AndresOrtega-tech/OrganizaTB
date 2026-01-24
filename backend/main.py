from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import logging

# Configuración de logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Intentar importaciones relativas o absolutas según el contexto de ejecución
try:
    from backend.database import supabase
    from backend.auth.api import router as auth_router
    from backend.tags.api import router as tags_router
except ImportError:
    from database import supabase
    from auth.api import router as auth_router
    from tags.api import router as tags_router

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
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(auth_router, prefix="/api", tags=["Authentication"])
app.include_router(tags_router, prefix="/api/tags", tags=["Tags"])

@app.get("/", tags=["Health"])
def read_root():
    return {"message": "Hola Mundo desde FastAPI en Vercel"}

@app.get("/health", tags=["Health"])
def health_check():
    try:
        return {
            "status": "ok",
            "supabase_connected": True if supabase else False,
            "supabase_url": str(supabase.supabase_url) if supabase else None
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "error", "detail": str(e)}

@app.get("/tables", tags=["Health"])
def list_tables():
    if supabase is None:
        return {
            "status": "error",
            "message": "Supabase no está configurado. Revisa las variables SUPABASE_URL y SUPABASE_ANON_KEY."
        }

    try:
        response = supabase.rpc("get_tables", {}).execute()
        return {"tables": response.data}
    except Exception as e:
        return {
            "status": "error",
            "message": "No se pudieron listar las tablas. Asegúrate de haber creado la función RPC en Supabase.",
            "details": str(e),
            "solution": "Ejecuta el SQL para crear get_tables()"
        }
