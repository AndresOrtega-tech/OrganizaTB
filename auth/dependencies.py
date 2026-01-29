from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
try:
    from backend.database import supabase
except ImportError:
    from database import supabase

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Valida el token JWT usando Supabase Auth y retorna el usuario autenticado.
    Espera un header Authorization: Bearer <token>
    """
    token = credentials.credentials
    try:
        # supabase.auth.get_user(token) valida el token y devuelve el usuario
        user_response = supabase.auth.get_user(token)
        
        if not user_response or not user_response.user:
             raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido o expirado",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user_response.user
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Error de autenticación: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
