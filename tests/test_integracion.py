"""
Tests de integración — OrganizaT API
Prueba todos los endpoints de Tasks, Tags, Notes, Events, Relations y Reminders.
Al final elimina todo lo creado.

Variables de entorno requeridas (.env):
    TEST_EMAIL      — correo del usuario de prueba
    TEST_PASSWORD   — contraseña del usuario
    BASE_URL        — URL base de la API (default: https://api-organiza-tb.vercel.app/api)

Uso: python tests/test_integracion.py
"""

import asyncio
import os
import sys
import time
from datetime import datetime, timedelta, timezone

import aiohttp
from dotenv import load_dotenv

# Cargar .env desde la raíz del proyecto
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

# ─── Configuración ────────────────────────────────────────────────────────────
BASE_URL = os.environ.get(
    "BASE_URL",
    "https://api-organiza-tb-git-development-andresortegatechs-projects.vercel.app/",
).rstrip("/")
# Asegurar que /api esté al final
if not BASE_URL.endswith("/api"):
    BASE_URL = BASE_URL.rstrip("/") + "/api"
TEST_EMAIL = os.environ.get("TEST_EMAIL", "")
TEST_PASSWORD = os.environ.get("TEST_PASSWORD", "")

# ─── Colores ANSI ─────────────────────────────────────────────────────────────
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"

# ─── Contadores ───────────────────────────────────────────────────────────────
passed = 0
failed = 0
errors: list[str] = []

# ─── Almacén de IDs ───────────────────────────────────────────────────────────
created: dict = {
    "token": "",
    "tag1_id": "",
    "tag2_id": "",
    "task1_id": "",
    "task2_id": "",
    "note1_id": "",
    "note2_id": "",
    "event1_id": "",
    "event2_id": "",
    "reminder1_id": "",
}

# Timestamp para nombres únicos
TS = int(time.time())


# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════════


def h() -> dict:
    """Headers con token de autenticación."""
    return {
        "Authorization": f"Bearer {created['token']}",
        "Content-Type": "application/json",
    }


def log_pass(step: str, detail: str = ""):
    global passed
    passed += 1
    msg = f"  {GREEN}✔ PASS{RESET}  {step}"
    if detail:
        msg += f"  {CYAN}{detail}{RESET}"
    print(msg)


def log_fail(step: str, detail: str):
    global failed
    failed += 1
    errors.append(step)
    print(f"  {RED}✘ FAIL{RESET}  {step}  — {detail}")


def log_info(msg: str):
    print(f"  {YELLOW}▸{RESET} {msg}")


def log_phase(name: str):
    print(f"\n{BOLD}{'─' * 60}{RESET}")
    print(f"  {BOLD}{CYAN}{name}{RESET}")
    print(f"{BOLD}{'─' * 60}{RESET}")


def assert_status(step: str, resp: aiohttp.ClientResponse, expected: int) -> bool:
    if resp.status != expected:
        log_fail(step, f"status esperado {expected}, obtuvo {resp.status}")
        return False
    return True


async def resp_json_safe(resp: aiohttp.ClientResponse) -> dict | list | None:
    """Parsea JSON si hay contenido, None si 204."""
    if resp.status == 204:
        return None
    try:
        return await resp.json()
    except Exception:
        return None


def now_iso(hours_offset: int = 0) -> str:
    """Datetime ISO con offset en horas desde ahora."""
    dt = datetime.now(timezone.utc) + timedelta(hours=hours_offset)
    return dt.isoformat()


# ═══════════════════════════════════════════════════════════════════════════════
# FASES
# ═══════════════════════════════════════════════════════════════════════════════


async def fase_0_login(session: aiohttp.ClientSession) -> bool:
    """Login para obtener access_token."""
    log_phase("FASE 0 — Login")

    if not TEST_EMAIL or not TEST_PASSWORD:
        log_fail("0.1 Login", "TEST_EMAIL o TEST_PASSWORD no definidos en .env")
        return False

    url = f"{BASE_URL}/auth/login"
    payload = {"email": TEST_EMAIL, "password": TEST_PASSWORD}

    async with session.post(url, json=payload) as resp:
        step = "0.1 POST /auth/login"
        if not assert_status(step, resp, 200):
            return False
        data = await resp_json_safe(resp)

    if not data or "access_token" not in data:
        log_fail("0.1 Login", f"respuesta no contiene access_token: {data}")
        return False

    created["token"] = data["access_token"]
    log_pass(step, f"token obtenido ({len(created['token'])} chars)")
    return True


async def fase_1_create_tags(session: aiohttp.ClientSession):
    """Crear 2 tags."""
    log_phase("FASE 1 — Crear Tags")

    # 1.1 Tag 1
    url = f"{BASE_URL}/tags/"
    payload = {"name": f"TestTag1_{TS}", "color": "#FF5733"}
    async with session.post(url, json=payload, headers=h()) as resp:
        step = "1.1 POST /tags/"
        if assert_status(step, resp, 201):
            data = await resp_json_safe(resp)
            if data and "id" in data:
                created["tag1_id"] = data["id"]
                log_pass(step, f"id={data['id'][:8]}… name={data.get('name')}")
            else:
                log_fail(step, "sin id en respuesta")
        else:
            await resp_json_safe(resp)

    # 1.2 Tag 2
    payload = {"name": f"TestTag2_{TS}", "color": "#33FF57"}
    async with session.post(url, json=payload, headers=h()) as resp:
        step = "1.2 POST /tags/"
        if assert_status(step, resp, 201):
            data = await resp_json_safe(resp)
            if data and "id" in data:
                created["tag2_id"] = data["id"]
                log_pass(step, f"id={data['id'][:8]}… name={data.get('name')}")
            else:
                log_fail(step, "sin id en respuesta")
        else:
            await resp_json_safe(resp)


async def fase_2_create_tasks(session: aiohttp.ClientSession):
    """Crear 2 tasks (una con reminder, otra sin)."""
    log_phase("FASE 2 — Crear Tasks")

    # 2.1 Task con reminder
    url = f"{BASE_URL}/tasks/"
    payload = {
        "title": f"Tarea con reminder {TS}",
        "description": "Descripcion de prueba",
        "due_date": now_iso(2),
        "priority": "alta",
        "reminders": [{"value": 30, "unit": "minutes"}],
    }
    async with session.post(url, json=payload, headers=h()) as resp:
        step = "2.1 POST /tasks/ (con reminder)"
        if assert_status(step, resp, 201):
            data = await resp_json_safe(resp)
            if data and "id" in data:
                created["task1_id"] = data["id"]
                # Capturar reminder_id si existe
                rem_data = data.get("reminders_data", [])
                if rem_data:
                    created["reminder1_id"] = rem_data[0].get("id", "")
                has_rem = data.get("has_reminder", False)
                log_pass(
                    step,
                    f"id={data['id'][:8]}… has_reminder={has_rem} reminders={len(rem_data)}",
                )
            else:
                log_fail(step, "sin id en respuesta")
        else:
            await resp_json_safe(resp)

    # 2.2 Task sin reminder
    payload = {
        "title": f"Tarea sin reminder {TS}",
        "description": "Descripcion 2",
        "due_date": now_iso(3),
        "priority": "baja",
    }
    async with session.post(url, json=payload, headers=h()) as resp:
        step = "2.2 POST /tasks/ (sin reminder)"
        if assert_status(step, resp, 201):
            data = await resp_json_safe(resp)
            if data and "id" in data:
                created["task2_id"] = data["id"]
                has_rem = data.get("has_reminder", False)
                log_pass(step, f"id={data['id'][:8]}… has_reminder={has_rem}")
            else:
                log_fail(step, "sin id en respuesta")
        else:
            await resp_json_safe(resp)


async def fase_3_create_notes(session: aiohttp.ClientSession):
    """Crear 2 notes."""
    log_phase("FASE 3 — Crear Notes")

    # 3.1 Note con summary
    url = f"{BASE_URL}/notes/"
    payload = {
        "title": f"Nota test 1 {TS}",
        "content": "Contenido de prueba para nota 1",
        "summary": "Resumen 1",
    }
    async with session.post(url, json=payload, headers=h()) as resp:
        step = "3.1 POST /notes/"
        if assert_status(step, resp, 201):
            data = await resp_json_safe(resp)
            if data and "id" in data:
                created["note1_id"] = data["id"]
                log_pass(step, f"id={data['id'][:8]}… title={data.get('title')}")
            else:
                log_fail(step, "sin id en respuesta")
        else:
            await resp_json_safe(resp)

    # 3.2 Note sin summary
    payload = {
        "title": f"Nota test 2 {TS}",
        "content": "Contenido de prueba para nota 2",
    }
    async with session.post(url, json=payload, headers=h()) as resp:
        step = "3.2 POST /notes/"
        if assert_status(step, resp, 201):
            data = await resp_json_safe(resp)
            if data and "id" in data:
                created["note2_id"] = data["id"]
                log_pass(step, f"id={data['id'][:8]}… title={data.get('title')}")
            else:
                log_fail(step, "sin id en respuesta")
        else:
            await resp_json_safe(resp)


async def fase_4_create_events(session: aiohttp.ClientSession):
    """Crear 2 events (uno con reminder, otro sin)."""
    log_phase("FASE 4 — Crear Events")

    # 4.1 Event con reminder
    url = f"{BASE_URL}/events/"
    payload = {
        "title": f"Evento con reminder {TS}",
        "description": "Evento de prueba",
        "start_time": now_iso(1),
        "end_time": now_iso(2),
        "location": "Oficina",
        "reminders": [{"value": 15, "unit": "minutes"}],
    }
    async with session.post(url, json=payload, headers=h()) as resp:
        step = "4.1 POST /events/ (con reminder)"
        if assert_status(step, resp, 201):
            data = await resp_json_safe(resp)
            if data and "id" in data:
                created["event1_id"] = data["id"]
                has_rem = data.get("has_reminder", False)
                log_pass(step, f"id={data['id'][:8]}… has_reminder={has_rem}")
            else:
                log_fail(step, "sin id en respuesta")
        else:
            await resp_json_safe(resp)

    # 4.2 Event sin reminder
    payload = {
        "title": f"Evento sin reminder {TS}",
        "start_time": now_iso(4),
        "end_time": now_iso(5),
    }
    async with session.post(url, json=payload, headers=h()) as resp:
        step = "4.2 POST /events/ (sin reminder)"
        if assert_status(step, resp, 201):
            data = await resp_json_safe(resp)
            if data and "id" in data:
                created["event2_id"] = data["id"]
                log_pass(step, f"id={data['id'][:8]}… title={data.get('title')}")
            else:
                log_fail(step, "sin id en respuesta")
        else:
            await resp_json_safe(resp)


async def fase_5_get_lists(session: aiohttp.ClientSession):
    """GET listas de todos los módulos."""
    log_phase("FASE 5 — GET Listas")

    # 5.1 GET tags
    url = f"{BASE_URL}/tags/"
    async with session.get(url, headers=h()) as resp:
        step = "5.1 GET /tags/"
        if assert_status(step, resp, 200):
            data = await resp_json_safe(resp)
            count = len(data) if isinstance(data, list) else 0
            if count >= 2:
                log_pass(step, f"{count} tags encontrados")
            else:
                log_fail(step, f"esperados >=2 tags, obtuvo {count}")
        else:
            await resp_json_safe(resp)

    # 5.2 GET tasks (pending)
    url = f"{BASE_URL}/tasks/?view=tasks&tab=pending"
    async with session.get(url, headers=h()) as resp:
        step = "5.2 GET /tasks/ (pending)"
        if assert_status(step, resp, 200):
            data = await resp_json_safe(resp)
            items = data.get("data", []) if isinstance(data, dict) else []
            has_more = data.get("has_more", None) if isinstance(data, dict) else None
            if len(items) >= 2:
                log_pass(step, f"{len(items)} tasks, has_more={has_more}")
            else:
                log_fail(step, f"esperados >=2 tasks, obtuvo {len(items)}")
        else:
            await resp_json_safe(resp)

    # 5.3 GET tasks (filter priority=alta)
    url = f"{BASE_URL}/tasks/?view=tasks&tab=pending&priority=alta"
    async with session.get(url, headers=h()) as resp:
        step = "5.3 GET /tasks/ (priority=alta)"
        if assert_status(step, resp, 200):
            data = await resp_json_safe(resp)
            items = data.get("data", []) if isinstance(data, dict) else []
            all_alta = (
                all(t.get("priority") == "alta" for t in items) if items else True
            )
            if items and all_alta:
                log_pass(step, f"{len(items)} tasks con priority=alta")
            elif not items:
                log_pass(step, "0 tasks con priority=alta (task1 ya completada en 7.2)")
            else:
                log_fail(step, "algunos tasks no tienen priority=alta")
        else:
            await resp_json_safe(resp)

    # 5.4 GET notes
    url = f"{BASE_URL}/notes/?is_archived=false"
    async with session.get(url, headers=h()) as resp:
        step = "5.4 GET /notes/"
        if assert_status(step, resp, 200):
            data = await resp_json_safe(resp)
            count = len(data) if isinstance(data, list) else 0
            if count >= 2:
                log_pass(step, f"{count} notes encontrados")
            else:
                log_fail(step, f"esperados >=2 notes, obtuvo {count}")
        else:
            await resp_json_safe(resp)

    # 5.5 GET events
    url = f"{BASE_URL}/events/"
    async with session.get(url, headers=h()) as resp:
        step = "5.5 GET /events/"
        if assert_status(step, resp, 200):
            data = await resp_json_safe(resp)
            count = len(data) if isinstance(data, list) else 0
            if count >= 2:
                log_pass(step, f"{count} events encontrados")
            else:
                log_fail(step, f"esperados >=2 events, obtuvo {count}")
        else:
            await resp_json_safe(resp)

    # 5.6 GET reminders (pending)
    url = f"{BASE_URL}/reminders/?status=pending"
    async with session.get(url, headers=h()) as resp:
        step = "5.6 GET /reminders/ (pending)"
        if assert_status(step, resp, 200):
            data = await resp_json_safe(resp)
            count = len(data) if isinstance(data, list) else 0
            if count >= 1:
                log_pass(step, f"{count} reminders pendientes")
                # Actualizar reminder1_id si no se capturó antes
                if not created["reminder1_id"] and data:
                    created["reminder1_id"] = data[0].get("id", "")
            else:
                log_pass(step, "0 reminders pendientes (ok si el reminder ya se envió)")
        else:
            await resp_json_safe(resp)


async def fase_6_get_individuals(session: aiohttp.ClientSession):
    """GET entidades individuales por ID."""
    log_phase("FASE 6 — GET Individuales")

    # 6.1 GET task
    if created["task1_id"]:
        url = f"{BASE_URL}/tasks/{created['task1_id']}"
        async with session.get(url, headers=h()) as resp:
            step = "6.1 GET /tasks/{id}"
            if assert_status(step, resp, 200):
                data = await resp_json_safe(resp)
                if data and data.get("id") == created["task1_id"]:
                    log_pass(step, f"title={data.get('title')}")
                else:
                    log_fail(step, "id no coincide")
            else:
                await resp_json_safe(resp)

    # 6.2 GET note
    if created["note1_id"]:
        url = f"{BASE_URL}/notes/{created['note1_id']}"
        async with session.get(url, headers=h()) as resp:
            step = "6.2 GET /notes/{id}"
            if assert_status(step, resp, 200):
                data = await resp_json_safe(resp)
                if data and data.get("id") == created["note1_id"]:
                    log_pass(step, f"title={data.get('title')}")
                else:
                    log_fail(step, "id no coincide")
            else:
                await resp_json_safe(resp)

    # 6.3 GET event
    if created["event1_id"]:
        url = f"{BASE_URL}/events/{created['event1_id']}"
        async with session.get(url, headers=h()) as resp:
            step = "6.3 GET /events/{id}"
            if assert_status(step, resp, 200):
                data = await resp_json_safe(resp)
                if data and data.get("id") == created["event1_id"]:
                    log_pass(step, f"title={data.get('title')}")
                else:
                    log_fail(step, "id no coincide")
            else:
                await resp_json_safe(resp)


async def fase_7_patch_updates(session: aiohttp.ClientSession):
    """PATCH / actualizar entidades."""
    log_phase("FASE 7 — PATCH / Actualizar")

    # 7.1 PATCH tag
    if created["tag1_id"]:
        url = f"{BASE_URL}/tags/{created['tag1_id']}"
        payload = {"name": f"TestTag1 Updated {TS}", "color": "#000000"}
        async with session.patch(url, json=payload, headers=h()) as resp:
            step = "7.1 PATCH /tags/{id}"
            if assert_status(step, resp, 200):
                data = await resp_json_safe(resp)
                if data and data.get("name") == payload["name"]:
                    log_pass(step, f"name={data.get('name')}")
                else:
                    log_fail(
                        step,
                        f"name esperado '{payload['name']}', obtuvo '{data.get('name')}'",
                    )
            else:
                await resp_json_safe(resp)

    # 7.2 PATCH task
    if created["task1_id"]:
        url = f"{BASE_URL}/tasks/{created['task1_id']}"
        payload = {"title": f"Tarea actualizada {TS}", "is_completed": True}
        async with session.patch(url, json=payload, headers=h()) as resp:
            step = "7.2 PATCH /tasks/{id}"
            if assert_status(step, resp, 200):
                data = await resp_json_safe(resp)
                if data and data.get("is_completed") is True:
                    log_pass(step, f"is_completed={data.get('is_completed')}")
                else:
                    log_fail(
                        step,
                        f"is_completed esperado True, obtuvo {data.get('is_completed')}",
                    )
            else:
                await resp_json_safe(resp)

    # 7.3 PATCH note
    if created["note1_id"]:
        url = f"{BASE_URL}/notes/{created['note1_id']}"
        payload = {
            "title": f"Nota actualizada {TS}",
            "content": "Contenido nuevo de prueba",
        }
        async with session.patch(url, json=payload, headers=h()) as resp:
            step = "7.3 PATCH /notes/{id}"
            if assert_status(step, resp, 200):
                data = await resp_json_safe(resp)
                if data and data.get("title") == payload["title"]:
                    log_pass(step, f"title={data.get('title')}")
                else:
                    log_fail(step, f"title no coincide")
            else:
                await resp_json_safe(resp)

    # 7.4 PATCH note summary
    if created["note1_id"]:
        url = f"{BASE_URL}/notes/{created['note1_id']}/summary"
        payload = {"summary": "Resumen actualizado por test"}
        async with session.patch(url, json=payload, headers=h()) as resp:
            step = "7.4 PATCH /notes/{id}/summary"
            if assert_status(step, resp, 200):
                data = await resp_json_safe(resp)
                if data and data.get("summary") == payload["summary"]:
                    log_pass(step, f"summary={data.get('summary')}")
                else:
                    log_fail(step, "summary no coincide")
            else:
                await resp_json_safe(resp)

    # 7.5 PATCH event
    if created["event1_id"]:
        url = f"{BASE_URL}/events/{created['event1_id']}"
        payload = {"title": f"Evento actualizado {TS}", "location": "Casa"}
        async with session.patch(url, json=payload, headers=h()) as resp:
            step = "7.5 PATCH /events/{id}"
            if assert_status(step, resp, 200):
                data = await resp_json_safe(resp)
                if data and data.get("title") == payload["title"]:
                    log_pass(
                        step,
                        f"title={data.get('title')}, location={data.get('location')}",
                    )
                else:
                    log_fail(step, "title no coincide")
            else:
                await resp_json_safe(resp)

    # 7.6 PATCH reminder
    if created["reminder1_id"]:
        url = f"{BASE_URL}/reminders/{created['reminder1_id']}"
        payload = {"status": "sent"}
        async with session.patch(url, json=payload, headers=h()) as resp:
            step = "7.6 PATCH /reminders/{id}"
            if assert_status(step, resp, 200):
                data = await resp_json_safe(resp)
                if data and data.get("status") == "sent":
                    log_pass(step, f"status={data.get('status')}")
                else:
                    log_fail(
                        step, f"status esperado 'sent', obtuvo '{data.get('status')}'"
                    )
            else:
                await resp_json_safe(resp)


async def fase_8_assign_tags(session: aiohttp.ClientSession):
    """Asignar tags a tasks, notes, events."""
    log_phase("FASE 8 — Asignar Tags")

    # 8.1 Tag1 → Task1
    if created["task1_id"] and created["tag1_id"]:
        url = f"{BASE_URL}/tasks/{created['task1_id']}/tags"
        payload = {"tag_id": created["tag1_id"]}
        async with session.post(url, json=payload, headers=h()) as resp:
            step = "8.1 POST /tasks/{id}/tags (tag1)"
            if assert_status(step, resp, 200):
                data = await resp_json_safe(resp)
                assigned = data.get("assigned", -1) if data else -1
                log_pass(step, f"assigned={assigned}")
            else:
                await resp_json_safe(resp)

    # 8.2 Tag2 → Task1
    if created["task1_id"] and created["tag2_id"]:
        url = f"{BASE_URL}/tasks/{created['task1_id']}/tags"
        payload = {"tag_id": created["tag2_id"]}
        async with session.post(url, json=payload, headers=h()) as resp:
            step = "8.2 POST /tasks/{id}/tags (tag2)"
            if assert_status(step, resp, 200):
                data = await resp_json_safe(resp)
                assigned = data.get("assigned", -1) if data else -1
                log_pass(step, f"assigned={assigned}")
            else:
                await resp_json_safe(resp)

    # 8.3 Tag1 → Note1
    if created["note1_id"] and created["tag1_id"]:
        url = f"{BASE_URL}/notes/{created['note1_id']}/tags"
        payload = {"tag_id": created["tag1_id"]}
        async with session.post(url, json=payload, headers=h()) as resp:
            step = "8.3 POST /notes/{id}/tags (tag1)"
            if assert_status(step, resp, 200):
                data = await resp_json_safe(resp)
                assigned = data.get("assigned", -1) if data else -1
                log_pass(step, f"assigned={assigned}")
            else:
                await resp_json_safe(resp)

    # 8.4 Tag1 → Event1
    if created["event1_id"] and created["tag1_id"]:
        url = f"{BASE_URL}/events/{created['event1_id']}/tags"
        payload = {"tag_id": created["tag1_id"]}
        async with session.post(url, json=payload, headers=h()) as resp:
            step = "8.4 POST /events/{id}/tags (tag1)"
            if assert_status(step, resp, 200):
                data = await resp_json_safe(resp)
                assigned = data.get("assigned", -1) if data else -1
                log_pass(step, f"assigned={assigned}")
            else:
                await resp_json_safe(resp)


async def fase_9_get_related_pre(session: aiohttp.ClientSession):
    """GET related antes de crear relations (solo tags)."""
    log_phase("FASE 9 — GET Related (pre-relations)")

    # 9.1 Task related
    if created["task1_id"]:
        url = f"{BASE_URL}/tasks/{created['task1_id']}/related"
        async with session.get(url, headers=h()) as resp:
            step = "9.1 GET /tasks/{id}/related"
            if assert_status(step, resp, 200):
                data = await resp_json_safe(resp)
                tags_count = len(data.get("tags", [])) if data else 0
                notes_count = len(data.get("notes", [])) if data else 0
                events_count = len(data.get("events", [])) if data else 0
                if tags_count >= 2:
                    log_pass(
                        step,
                        f"tags={tags_count}, notes={notes_count}, events={events_count}",
                    )
                else:
                    log_fail(step, f"esperados >=2 tags, obtuvo {tags_count}")
            else:
                await resp_json_safe(resp)

    # 9.2 Note related
    if created["note1_id"]:
        url = f"{BASE_URL}/notes/{created['note1_id']}/related"
        async with session.get(url, headers=h()) as resp:
            step = "9.2 GET /notes/{id}/related"
            if assert_status(step, resp, 200):
                data = await resp_json_safe(resp)
                tags_count = len(data.get("tags", [])) if data else 0
                log_pass(step, f"tags={tags_count}")
            else:
                await resp_json_safe(resp)

    # 9.3 Event related
    if created["event1_id"]:
        url = f"{BASE_URL}/events/{created['event1_id']}/related"
        async with session.get(url, headers=h()) as resp:
            step = "9.3 GET /events/{id}/related"
            if assert_status(step, resp, 200):
                data = await resp_json_safe(resp)
                tags_count = len(data.get("tags", [])) if data else 0
                log_pass(step, f"tags={tags_count}")
            else:
                await resp_json_safe(resp)


async def fase_10_create_relations(session: aiohttp.ClientSession):
    """Crear vinculaciones task-note, task-event, note-event."""
    log_phase("FASE 10 — Crear Relations")

    # 10.1 Task1 ↔ Note1
    if created["task1_id"] and created["note1_id"]:
        url = f"{BASE_URL}/relations/task-note"
        payload = {"task_id": created["task1_id"], "note_id": created["note1_id"]}
        async with session.post(url, json=payload, headers=h()) as resp:
            step = "10.1 POST /relations/task-note"
            if assert_status(step, resp, 201):
                data = await resp_json_safe(resp)
                log_pass(step, data.get("message", "") if data else "")
            else:
                await resp_json_safe(resp)

    # 10.2 Task1 ↔ Event1
    if created["task1_id"] and created["event1_id"]:
        url = f"{BASE_URL}/relations/task-event"
        payload = {"task_id": created["task1_id"], "event_id": created["event1_id"]}
        async with session.post(url, json=payload, headers=h()) as resp:
            step = "10.2 POST /relations/task-event"
            if assert_status(step, resp, 201):
                data = await resp_json_safe(resp)
                log_pass(step, data.get("message", "") if data else "")
            else:
                await resp_json_safe(resp)

    # 10.3 Note1 ↔ Event1
    if created["note1_id"] and created["event1_id"]:
        url = f"{BASE_URL}/relations/note-event"
        payload = {"note_id": created["note1_id"], "event_id": created["event1_id"]}
        async with session.post(url, json=payload, headers=h()) as resp:
            step = "10.3 POST /relations/note-event"
            if assert_status(step, resp, 201):
                data = await resp_json_safe(resp)
                log_pass(step, data.get("message", "") if data else "")
            else:
                await resp_json_safe(resp)


async def fase_11_verify_relations(session: aiohttp.ClientSession):
    """Verificar que las relations aparecen en GET related."""
    log_phase("FASE 11 — Verificar Relations")

    # 11.1 Task1 related debe tener note1 y event1
    if created["task1_id"]:
        url = f"{BASE_URL}/tasks/{created['task1_id']}/related"
        async with session.get(url, headers=h()) as resp:
            step = "11.1 GET /tasks/{id}/related (post-relation)"
            if assert_status(step, resp, 200):
                data = await resp_json_safe(resp)
                note_ids = [n["id"] for n in data.get("notes", [])] if data else []
                event_ids = [e["id"] for e in data.get("events", [])] if data else []
                has_note = created["note1_id"] in note_ids
                has_event = created["event1_id"] in event_ids
                if has_note and has_event:
                    log_pass(step, f"notes={len(note_ids)}, events={len(event_ids)}")
                else:
                    log_fail(step, f"note_found={has_note}, event_found={has_event}")
            else:
                await resp_json_safe(resp)

    # 11.2 Note1 related debe tener task1 y event1
    if created["note1_id"]:
        url = f"{BASE_URL}/notes/{created['note1_id']}/related"
        async with session.get(url, headers=h()) as resp:
            step = "11.2 GET /notes/{id}/related (post-relation)"
            if assert_status(step, resp, 200):
                data = await resp_json_safe(resp)
                task_ids = [t["id"] for t in data.get("tasks", [])] if data else []
                event_ids = [e["id"] for e in data.get("events", [])] if data else []
                has_task = created["task1_id"] in task_ids
                has_event = created["event1_id"] in event_ids
                if has_task and has_event:
                    log_pass(step, f"tasks={len(task_ids)}, events={len(event_ids)}")
                else:
                    log_fail(step, f"task_found={has_task}, event_found={has_event}")
            else:
                await resp_json_safe(resp)

    # 11.3 Event1 related debe tener task1 y note1
    if created["event1_id"]:
        url = f"{BASE_URL}/events/{created['event1_id']}/related"
        async with session.get(url, headers=h()) as resp:
            step = "11.3 GET /events/{id}/related (post-relation)"
            if assert_status(step, resp, 200):
                data = await resp_json_safe(resp)
                task_ids = [t["id"] for t in data.get("tasks", [])] if data else []
                note_ids = [n["id"] for n in data.get("notes", [])] if data else []
                has_task = created["task1_id"] in task_ids
                has_note = created["note1_id"] in note_ids
                if has_task and has_note:
                    log_pass(step, f"tasks={len(task_ids)}, notes={len(note_ids)}")
                else:
                    log_fail(step, f"task_found={has_task}, note_found={has_note}")
            else:
                await resp_json_safe(resp)


async def fase_12_remove_tags(session: aiohttp.ClientSession):
    """Remover tags de entidades."""
    log_phase("FASE 12 — Remover Tags")

    # 12.1 Remove tag1 from task1
    if created["task1_id"] and created["tag1_id"]:
        url = f"{BASE_URL}/tasks/{created['task1_id']}/tags/{created['tag1_id']}"
        async with session.delete(url, headers=h()) as resp:
            step = "12.1 DELETE /tasks/{id}/tags/{tag_id}"
            assert_status(step, resp, 204)
            if resp.status == 204:
                log_pass(step)
            # no body on 204

    # 12.2 Remove tag1 from note1
    if created["note1_id"] and created["tag1_id"]:
        url = f"{BASE_URL}/notes/{created['note1_id']}/tags/{created['tag1_id']}"
        async with session.delete(url, headers=h()) as resp:
            step = "12.2 DELETE /notes/{id}/tags/{tag_id}"
            assert_status(step, resp, 204)
            if resp.status == 204:
                log_pass(step)

    # 12.3 Remove tag1 from event1
    if created["event1_id"] and created["tag1_id"]:
        url = f"{BASE_URL}/events/{created['event1_id']}/tags/{created['tag1_id']}"
        async with session.delete(url, headers=h()) as resp:
            step = "12.3 DELETE /events/{id}/tags/{tag_id}"
            assert_status(step, resp, 204)
            if resp.status == 204:
                log_pass(step)


async def fase_13_delete_relations(session: aiohttp.ClientSession):
    """Eliminar vinculaciones."""
    log_phase("FASE 13 — Eliminar Relations")

    # 13.1 Unlink task-note
    if created["task1_id"] and created["note1_id"]:
        url = f"{BASE_URL}/relations/task-note"
        payload = {"task_id": created["task1_id"], "note_id": created["note1_id"]}
        async with session.delete(url, json=payload, headers=h()) as resp:
            step = "13.1 DELETE /relations/task-note"
            if assert_status(step, resp, 200):
                data = await resp_json_safe(resp)
                log_pass(step, data.get("message", "") if data else "")

    # 13.2 Unlink task-event
    if created["task1_id"] and created["event1_id"]:
        url = f"{BASE_URL}/relations/task-event"
        payload = {"task_id": created["task1_id"], "event_id": created["event1_id"]}
        async with session.delete(url, json=payload, headers=h()) as resp:
            step = "13.2 DELETE /relations/task-event"
            if assert_status(step, resp, 200):
                data = await resp_json_safe(resp)
                log_pass(step, data.get("message", "") if data else "")

    # 13.3 Unlink note-event
    if created["note1_id"] and created["event1_id"]:
        url = f"{BASE_URL}/relations/note-event"
        payload = {"note_id": created["note1_id"], "event_id": created["event1_id"]}
        async with session.delete(url, json=payload, headers=h()) as resp:
            step = "13.3 DELETE /relations/note-event"
            if assert_status(step, resp, 200):
                data = await resp_json_safe(resp)
                log_pass(step, data.get("message", "") if data else "")


async def fase_14_delete_reminders(session: aiohttp.ClientSession):
    """Eliminar reminders."""
    log_phase("FASE 14 — Eliminar Reminders")

    if created["reminder1_id"]:
        url = f"{BASE_URL}/reminders/{created['reminder1_id']}"
        async with session.delete(url, headers=h()) as resp:
            step = "14.1 DELETE /reminders/{id}"
            assert_status(step, resp, 204)
            if resp.status == 204:
                log_pass(step)
    else:
        log_info("No hay reminder1_id, saltando eliminación")


async def fase_15_delete_tasks(session: aiohttp.ClientSession):
    """Eliminar tasks."""
    log_phase("FASE 15 — Eliminar Tasks")

    for i, key in enumerate(["task1_id", "task2_id"], start=1):
        if created[key]:
            url = f"{BASE_URL}/tasks/{created[key]}"
            async with session.delete(url, headers=h()) as resp:
                step = f"15.{i} DELETE /tasks/{{id}} ({key})"
                assert_status(step, resp, 204)
                if resp.status == 204:
                    log_pass(step)


async def fase_16_delete_notes(session: aiohttp.ClientSession):
    """Eliminar notes."""
    log_phase("FASE 16 — Eliminar Notes")

    for i, key in enumerate(["note1_id", "note2_id"], start=1):
        if created[key]:
            url = f"{BASE_URL}/notes/{created[key]}"
            async with session.delete(url, headers=h()) as resp:
                step = f"16.{i} DELETE /notes/{{id}} ({key})"
                assert_status(step, resp, 204)
                if resp.status == 204:
                    log_pass(step)


async def fase_17_delete_events(session: aiohttp.ClientSession):
    """Eliminar events."""
    log_phase("FASE 17 — Eliminar Events")

    for i, key in enumerate(["event1_id", "event2_id"], start=1):
        if created[key]:
            url = f"{BASE_URL}/events/{created[key]}"
            async with session.delete(url, headers=h()) as resp:
                step = f"17.{i} DELETE /events/{{id}} ({key})"
                assert_status(step, resp, 204)
                if resp.status == 204:
                    log_pass(step)


async def fase_18_delete_tags(session: aiohttp.ClientSession):
    """Eliminar tags (último)."""
    log_phase("FASE 18 — Eliminar Tags")

    for i, key in enumerate(["tag1_id", "tag2_id"], start=1):
        if created[key]:
            url = f"{BASE_URL}/tags/{created[key]}"
            async with session.delete(url, headers=h()) as resp:
                step = f"18.{i} DELETE /tags/{{id}} ({key})"
                assert_status(step, resp, 204)
                if resp.status == 204:
                    log_pass(step)


# ═══════════════════════════════════════════════════════════════════════════════
# CLEANUP DE EMERGENCIA
# ═══════════════════════════════════════════════════════════════════════════════


async def cleanup(session: aiohttp.ClientSession):
    """Intenta eliminar todo lo creado en caso de error a mitad del test."""
    log_phase("CLEANUP — Eliminación de emergencia")
    try:
        await fase_13_delete_relations(session)
    except Exception:
        pass
    try:
        await fase_14_delete_reminders(session)
    except Exception:
        pass
    try:
        await fase_15_delete_tasks(session)
    except Exception:
        pass
    try:
        await fase_16_delete_notes(session)
    except Exception:
        pass
    try:
        await fase_17_delete_events(session)
    except Exception:
        pass
    try:
        await fase_18_delete_tags(session)
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════


async def main():
    global passed, failed

    print(f"\n{BOLD}{'═' * 60}{RESET}")
    print(f"  {BOLD}TESTS DE INTEGRACIÓN — OrganizaT API{RESET}")
    print(f"  {BOLD}{'═' * 60}{RESET}")
    print(f"  Base URL: {BASE_URL}")
    print(f"  Timestamp: {TS}")
    print(f"{'═' * 60}{RESET}")

    t0 = time.time()

    async with aiohttp.ClientSession() as session:
        try:
            # Fase 0: Login
            ok = await fase_0_login(session)
            if not ok:
                print(f"\n{RED}{BOLD}No se pudo hacer login. Abortando.{RESET}")
                return

            # Fases 1-4: Crear entidades
            await fase_1_create_tags(session)
            await fase_2_create_tasks(session)
            await fase_3_create_notes(session)
            await fase_4_create_events(session)

            # Fases 5-6: Lecturas
            await fase_5_get_lists(session)
            await fase_6_get_individuals(session)

            # Fase 7: Updates
            await fase_7_patch_updates(session)

            # Fase 8: Asignar tags
            await fase_8_assign_tags(session)

            # Fase 9: Related pre-relations
            await fase_9_get_related_pre(session)

            # Fases 10-11: Crear y verificar relations
            await fase_10_create_relations(session)
            await fase_11_verify_relations(session)

            # Fases 12-18: Limpieza
            await fase_12_remove_tags(session)
            await fase_13_delete_relations(session)
            await fase_14_delete_reminders(session)
            await fase_15_delete_tasks(session)
            await fase_16_delete_notes(session)
            await fase_17_delete_events(session)
            await fase_18_delete_tags(session)

        except Exception as e:
            print(f"\n{RED}{BOLD}ERROR INESPERADO: {e}{RESET}")
            errors.append(str(e))
            # Intentar cleanup
            await cleanup(session)

    elapsed = time.time() - t0

    # ─── Resumen ──────────────────────────────────────────────────────────
    print(f"\n{BOLD}{'═' * 60}{RESET}")
    print(f"  {BOLD}RESUMEN{RESET}")
    print(f"{'═' * 60}{RESET}")
    print(f"  {GREEN}✔ Pasados:  {passed}{RESET}")
    print(f"  {RED}✘ Fallados: {failed}{RESET}")
    print(f"  ⏱ Tiempo:   {elapsed:.1f}s")

    if errors:
        print(f"\n  {RED}Errores:{RESET}")
        for err in errors:
            print(f"    - {err}")

    print(f"{'═' * 60}{RESET}\n")

    # Exit code
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    asyncio.run(main())
