"""
Tests de integración — OrganizaT API
Smoke tests que verifican los endpoints principales contra la API viva en Vercel.

Requiere variables de entorno:
  BASE_URL      URL base de la API (ej. https://api-organiza-tb.vercel.app)
  TEST_EMAIL    Email del usuario de prueba
  TEST_PASSWORD Contraseña del usuario de prueba

Uso local:
  export BASE_URL=https://api-organiza-tb.vercel.app
  export TEST_EMAIL=...
  export TEST_PASSWORD=...
  pytest tests/test_integration_v1.py -v
"""

import os
import pytest
import httpx
from datetime import datetime, timedelta, timezone

# ─── Configuración ─────────────────────────────────────────────────────────────
BASE_URL = os.environ["BASE_URL"].rstrip("/")
TEST_EMAIL = os.environ["TEST_EMAIL"]
TEST_PASSWORD = os.environ["TEST_PASSWORD"]

TIMEOUT = 15  # segundos


# ─── Fixtures de sesión ────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def auth_token() -> str:
    """Login y retorna el access_token JWT para toda la sesión de tests."""
    resp = httpx.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
        timeout=TIMEOUT,
    )
    assert resp.status_code == 200, f"Login falló ({resp.status_code}): {resp.text}"
    return resp.json()["access_token"]


@pytest.fixture(scope="session")
def headers(auth_token: str) -> dict:
    return {"Authorization": f"Bearer {auth_token}"}


# ─── Health ────────────────────────────────────────────────────────────────────

def test_health():
    resp = httpx.get(f"{BASE_URL}/health", timeout=TIMEOUT)
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["supabase_connected"] is True


# ─── Tags CRUD ─────────────────────────────────────────────────────────────────

def test_tags_crud(headers):
    tag_id = None
    try:
        # Crear
        resp = httpx.post(
            f"{BASE_URL}/api/tags/",
            headers=headers,
            json={"name": "ci-test-tag", "color": "#FF0000"},
            timeout=TIMEOUT,
        )
        assert resp.status_code in (200, 201), f"Crear tag falló: {resp.text}"
        tag_id = resp.json()["id"]

        # Listar y verificar que la tag creada aparece
        resp = httpx.get(f"{BASE_URL}/api/tags/", headers=headers, timeout=TIMEOUT)
        assert resp.status_code == 200
        ids = [t["id"] for t in resp.json()]
        assert tag_id in ids

    finally:
        # Cleanup
        if tag_id:
            httpx.delete(f"{BASE_URL}/api/tags/{tag_id}", headers=headers, timeout=TIMEOUT)


# ─── Tasks CRUD ────────────────────────────────────────────────────────────────

def test_tasks_crud(headers):
    task_id = None
    due = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    try:
        # Crear
        resp = httpx.post(
            f"{BASE_URL}/api/tasks/",
            headers=headers,
            json={"title": "ci-test-task", "due_date": due, "priority": "baja"},
            timeout=TIMEOUT,
        )
        assert resp.status_code in (200, 201), f"Crear task falló: {resp.text}"
        task_id = resp.json()["id"]

        # Obtener por ID
        resp = httpx.get(f"{BASE_URL}/api/tasks/{task_id}", headers=headers, timeout=TIMEOUT)
        assert resp.status_code == 200
        assert resp.json()["id"] == task_id

        # Listar
        resp = httpx.get(f"{BASE_URL}/api/tasks/", headers=headers, timeout=TIMEOUT)
        assert resp.status_code == 200

    finally:
        # Cleanup
        if task_id:
            httpx.delete(f"{BASE_URL}/api/tasks/{task_id}", headers=headers, timeout=TIMEOUT)


# ─── Notes CRUD ────────────────────────────────────────────────────────────────

def test_notes_crud(headers):
    note_id = None
    try:
        # Crear
        resp = httpx.post(
            f"{BASE_URL}/api/notes/",
            headers=headers,
            json={"title": "ci-test-note", "content": "contenido de prueba CI"},
            timeout=TIMEOUT,
        )
        assert resp.status_code in (200, 201), f"Crear note falló: {resp.text}"
        note_id = resp.json()["id"]

        # Obtener por ID
        resp = httpx.get(f"{BASE_URL}/api/notes/{note_id}", headers=headers, timeout=TIMEOUT)
        assert resp.status_code == 200
        assert resp.json()["id"] == note_id

        # Listar
        resp = httpx.get(f"{BASE_URL}/api/notes/", headers=headers, timeout=TIMEOUT)
        assert resp.status_code == 200

    finally:
        # Cleanup
        if note_id:
            httpx.delete(f"{BASE_URL}/api/notes/{note_id}", headers=headers, timeout=TIMEOUT)


# ─── Events CRUD ───────────────────────────────────────────────────────────────

def test_events_crud(headers):
    event_id = None
    start = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    end = (datetime.now(timezone.utc) + timedelta(days=1, hours=1)).isoformat()
    try:
        # Crear
        resp = httpx.post(
            f"{BASE_URL}/api/events/",
            headers=headers,
            json={"title": "ci-test-event", "start_time": start, "end_time": end},
            timeout=TIMEOUT,
        )
        assert resp.status_code in (200, 201), f"Crear event falló: {resp.text}"
        event_id = resp.json()["id"]

        # Obtener por ID
        resp = httpx.get(f"{BASE_URL}/api/events/{event_id}", headers=headers, timeout=TIMEOUT)
        assert resp.status_code == 200
        assert resp.json()["id"] == event_id

        # Listar
        resp = httpx.get(f"{BASE_URL}/api/events/", headers=headers, timeout=TIMEOUT)
        assert resp.status_code == 200

    finally:
        # Cleanup
        if event_id:
            httpx.delete(f"{BASE_URL}/api/events/{event_id}", headers=headers, timeout=TIMEOUT)


# ─── Reminders list ────────────────────────────────────────────────────────────

def test_reminders_list(headers):
    resp = httpx.get(f"{BASE_URL}/api/reminders/", headers=headers, timeout=TIMEOUT)
    assert resp.status_code == 200
