from fastapi import APIRouter, HTTPException, status, Request
try:
    from backend.database import supabase
    from backend.auth.schemas import UserCreate, UserLogin, Token
except ImportError:
    from database import supabase
    from auth.schemas import UserCreate, UserLogin, Token
import logging

# Configurar logger
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/users", status_code=status.HTTP_201_CREATED, summary="Registrar nuevo usuario")
async def register_user(user: UserCreate, request: Request):
    """
    Registra un nuevo usuario en Supabase Auth y crea su entrada en la tabla profiles.
    """
    try:
        # 1. Crear usuario en Supabase Auth
        # Supabase Auth se encarga del hashing seguro de contraseñas automáticamente.
        auth_response = supabase.auth.sign_up({
            "email": user.email,
            "password": user.password,
            "options": {
                "data": {
                    "full_name": user.full_name,
                    "avatar_url": user.avatar_url
                }
            }
        })

        if not auth_response.user:
            # Si no hay usuario en la respuesta, algo falló (ej. confirmación requerida pero no configurada)
            raise HTTPException(status_code=400, detail="No se pudo registrar el usuario. Verifique los datos.")

        # 2. La tabla 'profiles' debería actualizarse automáticamente mediante un Trigger en Supabase (recomendado)
        # Pero si se requiere inserción manual o actualización de la columna 'Correo':
        # Nota: El ID del usuario en profiles debe coincidir con auth.users.id
        
        # Intentamos actualizar el perfil si ya existe (creado por trigger) o insertarlo
        try:
            profile_data = {
                "id": auth_response.user.id,
                "Correo": user.email, # Columna solicitada 'Corrreo'
                "updated_at": "now()"
            }
            if user.full_name:
                profile_data["full_name"] = user.full_name
            if user.avatar_url:
                profile_data["avatar_url"] = user.avatar_url

            # Upsert para manejar tanto si el trigger lo creó como si no
            supabase.table("profiles").upsert(profile_data).execute()
            
        except Exception as db_error:
            logger.error(f"Error actualizando perfil: {str(db_error)}")
            # No fallamos todo el registro si solo falla la actualización del perfil auxiliar, 
            # pero es bueno loguearlo. Opcionalmente hacer rollback (borrar usuario auth).

        return {
            "message": "Usuario registrado exitosamente", 
            "user": {
                "id": auth_response.user.id,
                "email": auth_response.user.email
            }
        }

    except Exception as e:
        # Manejo de errores de Supabase (ej. usuario ya existe)
        error_msg = str(e)
        if "User already registered" in error_msg:
            raise HTTPException(status_code=400, detail="El correo electrónico ya está registrado.")
        
        logger.error(f"Error en registro: {error_msg}")
        raise HTTPException(status_code=400, detail=f"Error en el registro: {error_msg}")


@router.post("/auth/login", response_model=Token, summary="Iniciar sesión")
async def login(user: UserLogin, request: Request):
    """
    Autentica al usuario contra Supabase y devuelve tokens JWT.
    """
    try:
        auth_response = supabase.auth.sign_in_with_password({
            "email": user.email,
            "password": user.password
        })

        if not auth_response.session:
            raise HTTPException(status_code=401, detail="Credenciales inválidas")

        return {
            "access_token": auth_response.session.access_token,
            "token_type": "bearer",
            "refresh_token": auth_response.session.refresh_token,
            "expires_in": auth_response.session.expires_in,
            "user": {
                "id": auth_response.user.id,
                "email": auth_response.user.email
            }
        }

    except Exception as e:
        logger.error(f"Error en login: {str(e)}")
        raise HTTPException(status_code=400, detail="Error en la autenticación. Verifique sus credenciales.")
