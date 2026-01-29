from fastapi import APIRouter, HTTPException, status, Request, Depends
try:
    from backend.database import supabase
    from backend.auth.schemas import UserCreate, UserLogin, Token, UserAvatarUpdate, CurrentUser
    from backend.auth.dependencies import get_current_user
except ImportError:
    from database import supabase
    from auth.schemas import UserCreate, UserLogin, Token, UserAvatarUpdate, CurrentUser
    from auth.dependencies import get_current_user
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

        # Obtener datos del perfil para incluir en la respuesta
        full_name = None
        avatar_url = None
        
        try:
            # Intentar obtener datos actualizados de la tabla profiles
            profile_res = supabase.table("profiles").select("full_name, avatar_url").eq("id", auth_response.user.id).single().execute()
            if profile_res.data:
                full_name = profile_res.data.get("full_name")
                avatar_url = profile_res.data.get("avatar_url")
        except Exception as e:
            logger.warning(f"No se pudo obtener datos extra del perfil: {e}")
            # Fallback a metadatos de auth si falla la consulta a profiles
            full_name = auth_response.user.user_metadata.get("full_name")
            avatar_url = auth_response.user.user_metadata.get("avatar_url")

        return {
            "access_token": auth_response.session.access_token,
            "token_type": "bearer",
            "refresh_token": auth_response.session.refresh_token,
            "expires_in": auth_response.session.expires_in,
            "user": {
                # ID excluido según requerimiento
                "email": auth_response.user.email,
                "full_name": full_name,
                "avatar_url": avatar_url
            }
        }

    except Exception as e:
        logger.error(f"Error en login: {str(e)}")
        raise HTTPException(status_code=400, detail="Error en la autenticación. Verifique sus credenciales.")


@router.get("/users/me", response_model=CurrentUser, summary="Obtener información del usuario autenticado")
async def get_current_user_info(user=Depends(get_current_user)):
    try:
        full_name = None
        avatar_url = None

        try:
            profile_res = supabase.table("profiles").select("full_name, avatar_url").eq("id", user.id).single().execute()
            if profile_res.data:
                full_name = profile_res.data.get("full_name")
                avatar_url = profile_res.data.get("avatar_url")
        except Exception as e:
            logger.warning(f"No se pudo obtener datos extra del perfil: {e}")
            full_name = user.user_metadata.get("full_name") if user.user_metadata else None
            avatar_url = user.user_metadata.get("avatar_url") if user.user_metadata else None

        return CurrentUser(
            email=user.email,
            full_name=full_name,
            avatar_url=avatar_url,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo información del usuario: {e}")
        raise HTTPException(status_code=400, detail="No se pudo obtener la información del usuario.")


@router.patch("/users/avatar", summary="Actualizar avatar del usuario")
async def update_avatar(avatar_update: UserAvatarUpdate, user=Depends(get_current_user)):
    """
    Actualiza la URL del avatar del usuario autenticado.
    Verifica que la URL sea única entre todos los usuarios.
    """
    try:
        user_id = user.id
        new_avatar_url = avatar_update.avatar_url

        # 1. Verificar unicidad del avatar_url (si se requiere que sea único globalmente)
        # Consultamos si existe algún perfil con ese avatar_url que NO sea el usuario actual
        existing_avatar = supabase.table("profiles").select("id").eq("avatar_url", new_avatar_url).neq("id", user_id).execute()
        
        if existing_avatar.data and len(existing_avatar.data) > 0:
            raise HTTPException(
                status_code=400, 
                detail="Esta URL de avatar ya está en uso por otro usuario."
            )

        # 2. Actualizar el perfil
        update_response = supabase.table("profiles").update({
            "avatar_url": new_avatar_url,
            "updated_at": "now()"
        }).eq("id", user_id).execute()

        # Opcional: Actualizar metadatos del usuario en Supabase Auth si es necesario
        # supabase.auth.update_user({"data": {"avatar_url": new_avatar_url}})

        return {
            "message": "Avatar actualizado exitosamente",
            "avatar_url": new_avatar_url
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error actualizando avatar: {e}")
        raise HTTPException(status_code=400, detail=f"No se pudo actualizar el avatar: {str(e)}")


@router.get("/users/me", summary="Obtener información del usuario autenticado")
async def get_me(user=Depends(get_current_user)):
    """
    Retorna la información del usuario actualmente autenticado.
    """
    try:
        # Consultar perfil completo en la tabla profiles
        # Usamos maybe_single() por si no existe el perfil aún (aunque debería)
        profile_res = supabase.table("profiles").select("*").eq("id", user.id).maybe_single().execute()
        
        user_data = {
            "id": user.id,
            "email": user.email,
            "full_name": None,
            "avatar_url": None
        }
        
        if profile_res.data:
            user_data["full_name"] = profile_res.data.get("full_name")
            user_data["avatar_url"] = profile_res.data.get("avatar_url")
        else:
             # Fallback a metadatos de auth
             user_data["full_name"] = user.user_metadata.get("full_name")
             user_data["avatar_url"] = user.user_metadata.get("avatar_url")
             
        return user_data

    except Exception as e:
        logger.error(f"Error fetching user me: {e}")
        raise HTTPException(status_code=400, detail="Error al obtener datos del usuario")
