---
alwaysApply: false
description: Cundo vayamos a modificar el frontend
---
# Reglas de Frontend (React Native / Expo)

## Stack Tecnológico
- **Framework:** React Native 0.81.5 con Expo SDK ~54.0.31.
- **Librería UI:** React 19.1.0.
- **Navegación:** `@react-navigation/stack`.
- **Almacenamiento Local:** `@react-native-async-storage/async-storage`.
- **Componentes Nativos:** `@react-native-community/datetimepicker`.
- **Web:** Soporte vía Expo Web.

## Estructura del Proyecto
- `src/screens/`: Pantallas completas de la aplicación.
- `src/components/`: Componentes reutilizables (Botones, Inputs).
- `src/api/`: Capa de servicio para comunicación con el Backend.
  - `client.js`: Wrapper de fetch con manejo de Auth headers.
  - `config.js`: Constantes y configuración.

## Desarrollo UI/UX
- **Diseño:** Interfaz moderna y limpia.
- **Simplicidad:** Si el proyecto es muy sencillo (web), usar HTML/CSS/JS plano. Si es app, React Native/Expo.
- **Componentes:**
  - Crear componentes modulares para elementos repetitivos.
  - Usar nombres descriptivos (`CreateTaskScreen`, `Input`, `Button`).

## Integración con Backend
- **Autenticación:**
  - Almacenar tokens (JWT) en `AsyncStorage`.
  - Manejar errores 401 (expiración de sesión) redirigiendo al Login.
- **API Client:** Centralizar llamadas en `src/api/` para fácil mantenimiento.
- **Manejo de Estados:** Usar hooks de React (`useState`, `useEffect`) para gestión local.

## Convenciones
- **Idioma:** Español para textos de UI y comentarios.
- **Archivos:** `PascalCase` para Componentes, `camelCase` para utilidades/hooks.
