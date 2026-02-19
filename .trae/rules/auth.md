---
alwaysApply: false
description: Reglas de autenticación con Supabase Auth.
---
# Auth
- Supabase Auth con JWT (Bearer).
- Validación de sesión vía supabase.auth.get_user(token) en dependencias.
- refresh_token para renovar sesión sin re-login.
- Perfiles se crean por trigger en profiles; evitar upserts manuales.
