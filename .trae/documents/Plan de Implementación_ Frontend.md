# Plan de Implementación: Frontend Móvil (OrganizaT)

Este documento detalla la estrategia de desarrollo para la aplicación móvil OrganizaT, utilizando **React Native con Expo** y comunicándose con el backend desplegado en Vercel.

## 1. Stack Tecnológico
- **Framework**: React Native + Expo (Desarrollo móvil multiplataforma).
- **Estilos**: NativeWind (Tailwind CSS para React Native) o StyleSheet estándar.
- **Navegación**: React Navigation (Stack & Tab Navigator).
- **Estado/Data Fetching**: TanStack Query (React Query) o Context API.
- **Iconos**: Expo Vector Icons (Lucide/Ionicons).
- **HTTP Client**: Axios o Fetch API.
- **Despliegue**: EAS (Expo Application Services).

## 2. Configuración de Entorno
- Variable de entorno: `EXPO_PUBLIC_API_URL` (configurada en `app.json` o `.env`).
- Backend URL: https://organiza-t-git-development-andresortegatechs-projects.vercel.app/api

## 3. Estructura de Pantallas (Screens)

### A. Autenticación (Stack Navigator)
*   **LoginScreen**: Formulario de correo y contraseña.
*   **RegisterScreen**: Registro de nuevos usuarios.
*   **WelcomeScreen**: Pantalla inicial de carga/bienvenida.

### B. App Principal (Tab Navigator)
*   **HomeScreen**: Dashboard con resumen de tareas y accesos rápidos.
*   **TasksScreen**: Listado completo de tareas con filtros (Tags, Fecha).
*   **CreateTaskScreen**: Formulario para agregar nuevas tareas (Botón flotante central).
*   **ProfileScreen**: Información del usuario y configuración.

### C. Modales y Pantallas Secundarias
*   **TaskDetailScreen**: Vista detallada de una tarea.
*   **EditProfileScreen**: Cambio de avatar y datos personales.

## 4. Componentes Clave (Reutilizables)
*   `TaskCard`: Componente visual para mostrar una tarea en lista.
*   `TagChip`: Pill visual para etiquetas.
*   `CustomInput` / `CustomButton`: Elementos de UI consistentes.
*   `ScreenLayout`: Wrapper para manejo de SafeArea y estilos base.

## 5. Integración con Backend
*   **Auth**: `/auth/login`, `/users` (Registro).
*   **Users**: `/users/me` (GET), `/users/avatar` (PATCH).
*   **Tasks**: CRUD completo.
*   **Tags**: Gestión de etiquetas.

## 6. Pasos de Implementación
1.  **Configuración EAS**: Generar `eas.json` y configurar proyecto en Expo dashboard.
2.  **Navegación**: Configurar Stack y Tab Navigators.
3.  **Auth Flow**: Pantallas de Login/Registro conectadas al backend.
4.  **Gestión de Tareas**: Listado y creación de tareas.
5.  **Perfil**: Visualización y edición de usuario.
6.  **Despliegue**: Configuración de builds para Android/iOS con EAS Build.
