from fastapi import APIRouter, HTTPException, status, Request, Depends
from fastapi.security import HTTPAuthorizationCredentials
try:
    from backend.database import supabase, url as supabase_url, key as supabase_key
    from backend.auth.schemas import UserCreate, UserLogin, Token, UserAvatarUpdate, CurrentUser, UserPasswordUpdate, UserPasswordResetRequest, RefreshTokenRequest
    from backend.auth.dependencies import get_current_user, security
except ImportError:
    from database import supabase, url as supabase_url, key as supabase_key
    from auth.schemas import UserCreate, UserLogin, Token, UserAvatarUpdate, CurrentUser, UserPasswordUpdate, UserPasswordResetRequest, RefreshTokenRequest
    from auth.dependencies import get_current_user, security
import logging
import httpx
from slowapi import Limiter
from slowapi.util import get_remote_address

# Configurar logger
logger = logging.getLogger(__name__)

router = APIRouter()        # Prefijo: /api/auth
users_router = APIRouter()  # Prefijo: /api/users

# Rate limiter para auth
auth_limiter = Limiter(key_func=get_remote_address)

@users_router.post("/", status_code=status.HTTP_201_CREATED, summary="Registrar nuevo usuario")
@auth_limiter.limit("5/minute")
async def register_user(user: UserCreate, request: Request):
    """
    Registra un nuevo usuario en Supabase Auth y crea su entrada en la tabla profiles.
    """
    try:
        errors = []

        # 1. Verificar unicidad del email en la tabla profiles
        try:
            existing_email_profile = supabase.table("profiles").select("id").eq("Correo", user.email).maybe_single().execute()
            if existing_email_profile.data:
                errors.append("El correo electrónico ya está registrado.")
        except Exception:
            # Si falla la consulta (ej. error de conexión), continuamos pero logueamos si es necesario
            pass

        # 2. Verificar unicidad del avatar en la tabla profiles (si se proporciona)
        if user.avatar:
            try:
                # Mapeo: Consultamos la columna 'avatar_url' usando el valor de 'avatar'
                existing_avatar_profile = supabase.table("profiles").select("id").eq("avatar_url", user.avatar).maybe_single().execute()
                if existing_avatar_profile.data:
                    errors.append("El nombre de avatar ya está en uso.")
            except Exception as e:
                # Importante: Si la columna no existe, esto lanzará error. 
                # Lo capturamos para no romper todo el registro, pero deberíamos alertar.
                logger.error(f"Error verificando avatar: {e}")
                # Opcional: Agregar error genérico a la lista si es crítico
                # errors.append("Error verificando disponibilidad del avatar.")
                pass
        
        if errors:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=", ".join(errors))

        # 3. Crear usuario en Supabase Auth
        auth_response = supabase.auth.sign_up({
            "email": user.email,
            "password": user.password,
            "options": {
                "emailRedirectTo": "https://web-app-organiza-t.vercel.app/",
                "data": {
                    "full_name": user.full_name,
                    # Guardamos también en metadata como avatar_url para consistencia
                    "avatar_url": user.avatar
                }
            }
        })

        # Nota: Las versiones recientes de supabase-py lanzan excepción en caso de error,
        # por lo que si llegamos aquí, auth_response debería ser válido.
        # Sin embargo, verificamos si tenemos usuario.

        if not auth_response.user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se pudo registrar el usuario. Verifique los datos.")

        # 4. La tabla 'profiles' debería actualizarse automáticamente mediante un Trigger en Supabase (recomendado)
        # Pero si se requiere inserción manual o actualización de la columna 'Correo':
        # Nota: El ID del usuario en profiles debe coincidir con auth.users.id
        
        # Intentamos actualizar el perfil si ya existe (creado por trigger) o insertarlo
        try:
            profile_data = {
                "id": auth_response.user.id,
                "Correo": user.email, # Columna solicitada 'Correo'
                "updated_at": "now()"
            }
            if user.full_name:
                profile_data["full_name"] = user.full_name
            if user.avatar:
                # Mapeo: Guardamos en la columna 'avatar_url'
                profile_data["avatar_url"] = user.avatar

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

    except HTTPException:
        raise # Re-raise HTTPException to be handled by FastAPI
    except Exception as e:
        logger.error(f"Error en registro: {str(e)}")
        raise HTTPException(status_code=400, detail="Error en el registro. Intente nuevamente.")


@router.post("/login", response_model=Token, summary="Iniciar sesión")
@auth_limiter.limit("10/minute")
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
        avatar = None
        
        try:
            # Intentar obtener datos actualizados de la tabla profiles (columna avatar_url)
            profile_res = supabase.table("profiles").select("full_name, avatar_url").eq("id", auth_response.user.id).single().execute()
            if profile_res.data:
                full_name = profile_res.data.get("full_name")
                # Mapeo: Asignamos avatar_url de DB a la variable avatar
                avatar = profile_res.data.get("avatar_url")
        except Exception as e:
            logger.warning(f"No se pudo obtener datos extra del perfil: {e}")
            # Fallback a metadatos de auth si falla la consulta a profiles
            full_name = auth_response.user.user_metadata.get("full_name")
            avatar = auth_response.user.user_metadata.get("avatar_url")

        return {
            "access_token": auth_response.session.access_token,
            "token_type": "bearer",
            "refresh_token": auth_response.session.refresh_token,
            "expires_in": auth_response.session.expires_in,
            "user": {
                # ID excluido según requerimiento
                "email": auth_response.user.email,
                "full_name": full_name,
                "avatar": avatar
            }
        }

    except Exception as e:
        logger.error(f"Error en login: {str(e)}")
        raise HTTPException(status_code=400, detail="Error en la autenticación. Verifique sus credenciales.")


@router.post("/auth/refresh", response_model=Token, summary="Renovar Access Token")
@auth_limiter.limit("20/minute")
async def refresh_token(request_data: RefreshTokenRequest):
    """
    Renueva el token de acceso usando un refresh token válido.
    Permite mantener la sesión activa sin pedir credenciales nuevamente.
    """
    try:
        # Supabase py client: refresh_session espera el token string
        # Nota: Dependiendo de la versión, puede ser refresh_session(token) o set_session(token)
        # Para supabase-py reciente usamos refresh_session
        auth_response = supabase.auth.refresh_session(request_data.refresh_token)

        if not auth_response.session:
            raise HTTPException(status_code=401, detail="Refresh token inválido o expirado")

        # Recuperar datos extra del perfil para mantener consistencia en la respuesta
        full_name = None
        avatar = None
        try:
            profile_res = supabase.table("profiles").select("full_name, avatar_url").eq("id", auth_response.user.id).single().execute()
            if profile_res.data:
                full_name = profile_res.data.get("full_name")
                avatar = profile_res.data.get("avatar_url")
        except Exception:
            full_name = auth_response.user.user_metadata.get("full_name")
            avatar = auth_response.user.user_metadata.get("avatar_url")

        return {
            "access_token": auth_response.session.access_token,
            "token_type": "bearer",
            "refresh_token": auth_response.session.refresh_token,
            "expires_in": auth_response.session.expires_in,
            "user": {
                "email": auth_response.user.email,
                "full_name": full_name,
                "avatar": avatar
            }
        }

    except Exception as e:
        logger.error(f"Error renovando token: {e}")
        raise HTTPException(status_code=401, detail="No se pudo renovar la sesión. Inicie sesión nuevamente.")


@users_router.get("/me", response_model=CurrentUser, summary="Obtener información del usuario autenticado")
async def get_current_user_info(user=Depends(get_current_user)):
    try:
        full_name = None
        avatar = None

        try:
            # Mapeo: Consultamos avatar_url
            profile_res = supabase.table("profiles").select("full_name, avatar_url").eq("id", user.id).single().execute()
            if profile_res.data:
                full_name = profile_res.data.get("full_name")
                avatar = profile_res.data.get("avatar_url")
        except Exception as e:
            logger.warning(f"No se pudo obtener datos extra del perfil: {e}")
            full_name = user.user_metadata.get("full_name") if user.user_metadata else None
            avatar = user.user_metadata.get("avatar_url") if user.user_metadata else None

        return CurrentUser(
            email=user.email,
            full_name=full_name,
            avatar=avatar,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo información del usuario: {e}")
        raise HTTPException(status_code=400, detail="No se pudo obtener la información del usuario.")


@users_router.patch("/avatar", summary="Actualizar avatar del usuario")
async def update_avatar(avatar_update: UserAvatarUpdate, user=Depends(get_current_user)):
    """
    Actualiza el avatar del usuario autenticado.
    Verifica que el avatar sea único entre todos los usuarios.
    """
    try:
        user_id = user.id
        new_avatar = avatar_update.avatar

        # 1. Verificar unicidad del avatar (si se requiere que sea único globalmente)
        # Consultamos si existe algún perfil con ese avatar que NO sea el usuario actual
        # Mapeo: Consultamos avatar_url
        existing_avatar = supabase.table("profiles").select("id").eq("avatar_url", new_avatar).neq("id", user_id).execute()
        
        if existing_avatar.data and len(existing_avatar.data) > 0:
            raise HTTPException(
                status_code=400, 
                detail="Este nombre de avatar ya está en uso por otro usuario."
            )

        # 2. Actualizar el perfil
        # Mapeo: Actualizamos avatar_url
        update_response = supabase.table("profiles").update({
            "avatar_url": new_avatar,
            "updated_at": "now()"
        }).eq("id", user_id).execute()

        # Opcional: Actualizar metadatos del usuario en Supabase Auth si es necesario
        # supabase.auth.update_user({"data": {"avatar_url": new_avatar}})

        return {
            "message": "Avatar actualizado exitosamente",
            "avatar": new_avatar
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error actualizando avatar: {e}")
        raise HTTPException(status_code=400, detail="No se pudo actualizar el avatar.")


@users_router.patch("/password", summary="Cambiar contraseña (Usuario autenticado)")
async def update_password(
    password_update: UserPasswordUpdate, 
    user=Depends(get_current_user),
    token_data: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Permite a un usuario autenticado cambiar su contraseña.
    Requiere que el usuario haya iniciado sesión (JWT).
    """
    try:
        # Usamos httpx para hacer una petición directa a la API de Auth de Supabase
        # Esto nos permite actuar como el usuario usando su token bearer.
        token = token_data.credentials
        
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{supabase_url}/auth/v1/user",
                headers={
                    "Authorization": f"Bearer {token}",
                    "apikey": supabase_key,
                    "Content-Type": "application/json"
                },
                json={"password": password_update.password}
            )
            
            if response.status_code != 200:
                raise Exception(f"Error Supabase Auth: {response.text}")

        return {"message": "Contraseña actualizada exitosamente"}

    except Exception as e:
        logger.error(f"Error actualizando contraseña: {e}")
        raise HTTPException(status_code=400, detail="No se pudo actualizar la contraseña.")


@users_router.post("/password/reset", summary="Solicitar cambio de contraseña")
@auth_limiter.limit("3/minute")
async def request_password_reset(reset_request: UserPasswordResetRequest, request: Request):
    """
    Envía un correo al usuario especificado para restablecer su contraseña.
    No requiere autenticación previa.
    """
    try:
        # Enviar correo de restablecimiento
        # La redirección apunta a la app web para que el usuario ingrese su nueva clave
        supabase.auth.reset_password_email(reset_request.email, options={
            "redirect_to": "https://web-app-organiza-t.vercel.app/update-password"
        })

        return {"message": "Si el correo está registrado, se ha enviado un enlace para restablecer tu contraseña."}

    except Exception as e:
        logger.error(f"Error solicitando cambio de contraseña: {e}")
        raise HTTPException(status_code=400, detail="Error solicitando cambio de contraseña.")

