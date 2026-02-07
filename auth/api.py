from fastapi import APIRouter, HTTPException, status, Request, Depends
try:
    from backend.database import supabase
    from backend.auth.schemas import UserCreate, UserLogin, Token, UserAvatarUpdate, CurrentUser, UserPasswordUpdate, UserPasswordRecover
    from backend.auth.dependencies import get_current_user
except ImportError:
    from database import supabase
    from auth.schemas import UserCreate, UserLogin, Token, UserAvatarUpdate, CurrentUser, UserPasswordUpdate, UserPasswordRecover
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
        raise HTTPException(status_code=400, detail=f"Error en el registro: {str(e)}")


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


@router.get("/users/me", response_model=CurrentUser, summary="Obtener información del usuario autenticado")
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


@router.patch("/users/avatar", summary="Actualizar avatar del usuario")
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
        raise HTTPException(status_code=400, detail=f"No se pudo actualizar el avatar: {str(e)}")


@router.patch("/users/password", summary="Cambiar contraseña")
async def change_password(password_update: UserPasswordUpdate, user=Depends(get_current_user)):
    """
    Permite al usuario autenticado cambiar su contraseña.
    """
    try:
        # Actualizar contraseña en Supabase Auth
        # update_user actualiza el usuario asociado al token JWT actual
        response = supabase.auth.update_user({
            "password": password_update.password
        })

        if not response.user:
             raise HTTPException(status_code=400, detail="No se pudo actualizar la contraseña.")

        return {"message": "Contraseña actualizada exitosamente"}

    except Exception as e:
        logger.error(f"Error cambiando contraseña: {e}")
        raise HTTPException(status_code=400, detail=f"Error cambiando contraseña: {str(e)}")


@router.post("/auth/recovery", summary="Solicitar recuperación de contraseña")
async def recover_password(recover_data: UserPasswordRecover):
    """
    Envía un correo electrónico al usuario con un enlace para restablecer su contraseña.
    """
    try:
        email = recover_data.email
        redirect_url = "https://web-app-organiza-t.vercel.app/" # O una ruta específica como /reset-password

        response = supabase.auth.reset_password_email(email, options={
            "redirectTo": redirect_url
        })

        # Supabase no siempre retorna un error explícito si el email no existe (por seguridad)
        # pero asumimos éxito si no hay excepción.
        
        return {"message": "Si el correo está registrado, se ha enviado un enlace de recuperación."}

    except Exception as e:
        logger.error(f"Error en recuperación de contraseña: {e}")
        # Retornamos mensaje genérico por seguridad o el error si estamos en debug
        raise HTTPException(status_code=400, detail="Error procesando la solicitud de recuperación.")


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
            "avatar": None
        }
        
        if profile_res.data:
            user_data["full_name"] = profile_res.data.get("full_name")
            # Mapeo: avatar_url -> avatar
            user_data["avatar"] = profile_res.data.get("avatar_url")
        else:
             # Fallback a metadatos de auth
             user_data["full_name"] = user.user_metadata.get("full_name")
             user_data["avatar"] = user.user_metadata.get("avatar_url")
             
        return user_data

    except Exception as e:
        logger.error(f"Error fetching user me: {e}")
        raise HTTPException(status_code=400, detail="Error al obtener datos del usuario")
