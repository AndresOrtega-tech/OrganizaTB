# Plan de Implementación: Frontend (OrganizaT)

Este documento detalla la estrategia de desarrollo para la interfaz de usuario de la aplicación OrganizaT, siguiendo la arquitectura de React Native (Expo) y comunicándose con el backend desplegado en Vercel.

## 1. Stack Tecnológico
- **Framework**: React Native + Expo.
- **Estilos**: StyleSheet estándar de RN (Diseño responsivo y limpio).
- **Estado/Data Fetching**: `useState`, `useEffect`, `useCallback` y `useFocusEffect` (gestión de recargas y foco).
- **Navegación**: React Navigation (Stack Navigator).
- **Almacenamiento Local**: `@react-native-async-storage/async-storage` (Tokens JWT).
- **Componentes UI**:
  - `@react-native-community/datetimepicker` (Selector de fecha nativo).
  - Componentes propios: `Input`, `Button`.
- **HTTP Client**: `fetch` wrapper personalizado (`client.js`) con manejo de headers y errores 401.

## 2. Configuración de Entorno
- La aplicación se comunica directamente con la API desplegada en Vercel.
- Archivo `src/api/config.js` maneja la URL base.

## 3. Estructura de Pantallas (Vistas)

### A. Autenticación [COMPLETADO]
*   **Login**: Formulario de correo y contraseña. Guardado seguro de token.
*   **Register**: Registro de nuevos usuarios.
*   **Manejo de Sesión**: Auto-logout si el token expira (Error 401).

### B. Usuario [COMPLETADO]
*   **Perfil de Usuario**:
    *   Ver información del usuario (Nombre, Email, Avatar).
    *   **Cambiar Avatar**: Funcionalidad para actualizar la URL del avatar.
    *   **Logout**: Botón para cerrar sesión y limpiar storage.

### C. Gestión de Tareas (Dashboard Principal) [EN PROGRESO]
*   **HomeScreen**:
    *   Lista de tareas con pull-to-refresh.
    *   Visualización de estado (badges) y fecha de vencimiento.
    *   Botón flotante (FAB) para crear tareas.
*   **TaskDetailScreen**:
    *   Vista detallada de una tarea (Descripción, Tags, Estado).
*   **CreateTaskScreen**:
    *   Formulario con validaciones.
    *   Selector de fecha nativo (Date Picker).
    *   Switch para recordatorios.
    *   Etiquetas en inputs para mejor UX.

### D. Formularios y Acciones
*   **Agregar Tarea**: Completado.
*   **Agregar Tag**: Pendiente.
*   **Relacionar Tareas y Tags**: Visualización implementada, edición pendiente.

## 4. Componentes Clave (Reutilizables)
*   `Input`: Campo de texto con soporte para etiquetas (Label) y multiline.
*   `Button`: Botón estandarizado con estados de carga.
*   `TagBadge`: Visualización de etiquetas en listas.

## 5. Integración con Backend (Endpoints Implementados)
*   **Auth**: Login, Register.
*   **Users**: Get Me, Update Avatar.
*   **Tasks**: Get All, Get By ID, Create.

## 6. Pasos de Implementación (Estado Actual)
1.  **Setup Inicial**: [COMPLETADO] Estructura base Expo y React Navigation.
2.  **Auth Flow**: [COMPLETADO] Login, Registro, Logout y Persistencia de sesión.
3.  **Layout Base**: [COMPLETADO] Stack Navigator y estilos base.
4.  **CRUD Tareas**:
    *   Lectura (Listado y Detalle): [COMPLETADO]
    *   Creación: [COMPLETADO]
    *   Actualización/Eliminación: [PENDIENTE]
5.  **Gestión de Tags**: [PENDIENTE]
6.  **Integración Tareas-Tags**: [PARCIAL] (Solo visualización).
7.  **Vistas Avanzadas**: [PENDIENTE] (Filtros, Calendario).
8.  **Perfil**: [COMPLETADO]
