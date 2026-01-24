# Plan de Implementación: Frontend (OrganizaT)

Este documento detalla la estrategia de desarrollo para la interfaz de usuario de la aplicación OrganizaT, siguiendo la arquitectura de React + Vite y comunicándose con el backend desplegado en Vercel.

## 1. Stack Tecnológico
- **Framework**: React + Vite (Velocidad y modularidad).
- **Estilos**: Tailwind CSS (Desarrollo rápido y responsivo).
- **Estado/Data Fetching**: TanStack Query (React Query) o `useEffect` simple para inicio (gestión eficiente de caché y estados de carga).
- **Routing**: React Router DOM.
- **Iconos**: Lucide React o Heroicons.
- **HTTP Client**: Axios (configurado con interceptores para JWT).

## 2. Configuración de Entorno
- La aplicación se comunicará directamente con la API desplegada en Vercel.
- Variable de entorno: `VITE_API_URL` (se configurará con la URL de producción).

## 3. Estructura de Pantallas (Vistas)

### A. Autenticación
*   **Login**: Formulario de correo y contraseña. Manejo de tokens JWT.
*   **Signup**: Registro de nuevos usuarios (Nombre, Correo, Contraseña).

### B. Usuario
*   **Perfil de Usuario**:
    *   Ver información del usuario.
    *   **Cambiar Avatar**: Funcionalidad para actualizar la foto de perfil.

### C. Gestión de Tareas (Dashboard Principal)
*   **Vistas de Visualización**:
    *   **Lista por Defecto**: Tareas ordenadas por creación/importancia.
    *   **Lista por Tags**: Agrupación de tareas según sus etiquetas.
    *   **Lista por Fecha**: Orden cronológico (vencimiento).
    *   **Lista por Modificación**: Tareas editadas recientemente.
    *   **Calendario**: Vista mensual/semanal de tareas con fecha de vencimiento.

### D. Formularios y Acciones
*   **Agregar Tarea**: Formulario completo (Título, Descripción, Fecha, Tags).
*   **Agregar Tag**: Creación de nuevas etiquetas (Nombre, Color).
*   **Relacionar Tareas y Tags**: Interfaz para asignar o desasignar tags a una tarea existente o durante su creación.

## 4. Componentes Clave (Reutilizables)
*   `TaskCard`: Tarjeta individual de tarea con acciones rápidas (completar, editar, eliminar).
*   `TagBadge`: Pill/Etiqueta visual para los tags.
*   `Navbar/Sidebar`: Navegación principal.
*   `Modal`: Para formularios emergentes (crear tarea/tag sin salir de la vista).

## 5. Integración con Backend (Endpoints Previstos)
*   **Auth**: `/auth/login`, `/auth/register`.
*   **Users**: `/users/me` (GET, PATCH).
*   **Tasks**: GET `/tasks`, POST `/tasks`, PUT `/tasks/{id}`, DELETE `/tasks/{id}`.
*   **Tags**: GET `/tags`, POST `/tags`.
*   **Task-Tags**: Endpoints para asociar tags a tareas.

## 6. Pasos de Implementación
1.  **Setup Inicial**: Crear proyecto Vite, configurar Tailwind y React Router.
2.  **Auth Flow**: Implementar Login/Signup y guardado de Token.
3.  **Layout Base**: Navbar y estructura principal.
4.  **CRUD Tareas**: Visualización básica y creación.
5.  **Gestión de Tags**: Creación y listado de tags.
6.  **Integración Tareas-Tags**: Lógica para relacionar entidades.
7.  **Vistas Avanzadas**: Implementar filtros (Fecha, Modificación) y Calendario.
8.  **Perfil**: Edición de avatar y datos.
