# Plan de Implementación: Futuras Mejoras (IA y Recordatorios)

**Estado**: *Pendiente (Fase 2)*. Estas funcionalidades se implementarán una vez que la versión base (Frontend + Backend actual) esté confirmada y funcional.

## 1. Objetivo
Incorporar inteligencia artificial para la gestión de tareas y un sistema robusto de recordatorios automatizados, priorizando una experiencia de usuario fluida y "Human-in-the-Loop" (supervisión humana).

## 2. Cambios en Base de Datos (Esquemas)
*   **Tareas (`tasks`)**:
    *   Agregar columna `reminderTime` (DateTime) para configurar cuándo enviar la alerta.
*   **Usuarios (`users` / `profiles`)**:
    *   Agregar columna `phone` (String) para envío de WhatsApp.
    *   Agregar estado `phone_verified` (Boolean).

## 3. Arquitectura de Recordatorios
*   **Tecnología**: Vercel Cron Jobs + Supabase.
*   **Flujo**:
    1.  Vercel Cron invoca un endpoint seguro del backend cada X minutos.
    2.  El backend consulta tareas con `reminderTime` en el rango actual.
    3.  Se envían notificaciones vía Email (SMTP/API) y WhatsApp (API Business/Twillio/Meta) si el usuario tiene teléfono verificado.

## 4. Funcionalidades de IA (Human-in-the-Loop)

### A. Creación de Tareas Asistida
*   **Input**: El usuario envía Foto, Audio o Texto libre desde la App Móvil.
*   **Procesamiento**:
    *   Endpoint `/api/ai/parse-task` recibe el input.
    *   LLM (GPT/Gemini) extrae estructura JSON (Título, Descripción, Fecha, Tags sugeridos).
*   **Validación (Frontend)**:
    *   La App **no guarda automáticamente**.
    *   Renderiza el formulario de "Crear Tarea" pre-llenado con la data de la IA.
    *   Usuario revisa, edita si es necesario, y confirma ("Guardar").

### B. Modificación Semántica de Tareas
*   **Búsqueda**: Implementación de `pgvector` en Supabase para búsqueda semántica.
*   **Caso de Uso**: Usuario dice "Mueve la reunión de marketing para mañana".
    *   IA busca vectorialmente tareas relacionadas con "reunión marketing".
    *   Identifica la tarea correcta.
    *   Propone el cambio (JSON con nuevos valores).
*   **Validación**:
    *   App muestra: "Voy a cambiar 'Reunión Mkt' al [Nueva Fecha]. ¿Confirmar?".
    *   Usuario confirma o rechaza.

## 5. Estrategia de Despliegue Gradual
1.  **Backend Update**: Modificar esquemas DB y desplegar.
2.  **Recordatorios Email**: Activar cron jobs solo para email.
3.  **Integración IA Texto**: Habilitar parsing de texto en frontend.
4.  **Integración Multimedia**: Agregar soporte para audio/foto.
5.  **WhatsApp**: Habilitar campo teléfono y notificaciones móviles.
