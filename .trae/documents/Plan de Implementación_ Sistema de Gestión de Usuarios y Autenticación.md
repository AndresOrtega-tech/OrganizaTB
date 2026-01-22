Esta solución implementará un sistema de autenticación completo usando FastAPI y Supabase, siguiendo tus requerimientos de seguridad y escalabilidad.

### 1. Preparación y Dependencias

* **Instalar** **`slowapi`**: Para implementar el "Rate Limiting" (límite de peticiones) requerido.

* **Corrección de Variables de Entorno**: Alinear los nombres en `database.py` (`ANON_KEY` vs `ANON-KEY`) para asegurar la conexión con Supabase.

### 2. Base de Datos (Supabase)

Como no puedo ejecutar comandos SQL de estructura (DDL) directamente desde el código Python de forma segura sin un driver específico, te proporcionaré el **script SQL** necesario para que lo ejecutes en el panel de Supabase.

* **Tabla** **`profiles`**: Se modificará para incluir la columna `Correo` (VARCHAR 255, UNIQUE, NOT NULL) y se vinculará con la tabla de usuarios de Supabase (`auth.users`).

### 3. Implementación del Backend (Estructura de Archivos)

#### A. Modelos y Esquemas (`backend/auth/schemas.py`)

Definiremos los contratos de datos (Pydantic models) para validación automática:

* **`UserCreate`**: Para el registro (email, password, datos de perfil).

* **`UserLogin`**: Para el inicio de sesión.

* **`Token`**: Estructura de la respuesta JWT.

* **`Profile`**: Modelo de datos del perfil de usuario.

#### B. Endpoints de Autenticación (`backend/auth/api.py`)

Implementaremos el router `auth_router` con la lógica de negocio:

* **`POST /api/users`** **(Registro)**:

  1. Crea el usuario en Supabase Auth (`supabase.auth.sign_up`).
  2. Inserta los datos adicionales (incluyendo `Correo`) en la tabla `public.profiles`.
  3. Maneja errores como "Usuario ya registrado" o datos inválidos.
  4. Retorna `201 Created`.

* **`POST /api/login`** **(Login)**:

  1. Autentica contra Supabase (`supabase.auth.sign_in_with_password`).
  2. Retorna el Access Token y Refresh Token.

#### C. Integración Principal (`backend/main.py`)

Configuraremos el servidor FastAPI para producción:

* **CORS**: Configuración para permitir peticiones desde el frontend.

* **Rate Limiting**: Protección contra abuso (ej. 5 peticiones/minuto en login).

* **Inclusión de Rutas**: Conectar los nuevos endpoints de autenticación.

### 4. Seguridad y Buenas Prácticas

* **Hashing**: Delegado a Supabase Auth (Bcrypt/Argon2 implícito).

* **Validación**: Estricta mediante Pydantic.

* **Documentación**: Swagger UI estará disponible automáticamente en `/docs`.

¿Procedo con la implementación de este plan?
