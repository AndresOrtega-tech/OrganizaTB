"""
Pruebas de estrés — OrganizaT API
Ejecuta ~477 requests concurrentes con 3 usuarios en 5 fases.
Uso: python tests/pruebas_estres_v1.py
"""

import asyncio
import aiohttp
import time
import random
import csv
import os
from datetime import datetime, timedelta

# ─── Configuración ────────────────────────────────────────────────────────────
BASE_URL = "https://api-organiza-tb.vercel.app/api"

# JWTs por usuario (reemplazar con tokens válidos antes de correr)
TOKENS = {
    "user1": "eyJhbGciOiJFUzI1NiIsImtpZCI6IjRkYjg1ZGY5LTc5NDItNGFjMy04MzQzLWU2MjY4ZGVlYmMwNyIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJodHRwczovL3BteXN5dG11c3F1bmtlbnh6b3FtLnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiIzOWVkMjAxZS1hN2I2LTQ0NGYtODA3Ny04ODBjMWI0NTc3ZWEiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzcyMDczNTc2LCJpYXQiOjE3NzIwNjk5NzYsImVtYWlsIjoidXNlcnRlc3Q0QGdtYWlsLmNvbSIsInBob25lIjoiIiwiYXBwX21ldGFkYXRhIjp7InByb3ZpZGVyIjoiZW1haWwiLCJwcm92aWRlcnMiOlsiZW1haWwiXX0sInVzZXJfbWV0YWRhdGEiOnsiZW1haWxfdmVyaWZpZWQiOnRydWV9LCJyb2xlIjoiYXV0aGVudGljYXRlZCIsImFhbCI6ImFhbDEiLCJhbXIiOlt7Im1ldGhvZCI6InBhc3N3b3JkIiwidGltZXN0YW1wIjoxNzcyMDY5OTc2fV0sInNlc3Npb25faWQiOiI4OWNiZmZkNi1kNTliLTQ0OTctYTM4My0yZjE3OTQ0ZGUwZDAiLCJpc19hbm9ueW1vdXMiOmZhbHNlfQ.dzpi5aP5xWYR8AUuySIxBMTwcZZnHp6xE-ujrW-GxNDj_Q1tUBqYSo6ESAo0HUglcXdWG0qrfh8ZGCSGLFx25A",
    "user2": "eyJhbGciOiJFUzI1NiIsImtpZCI6IjRkYjg1ZGY5LTc5NDItNGFjMy04MzQzLWU2MjY4ZGVlYmMwNyIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJodHRwczovL3BteXN5dG11c3F1bmtlbnh6b3FtLnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiI3MzdiNTMwYy05ODBhLTQwYWEtYTZhZC1iMzM0ZGRkNmRjYmQiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzcyMDczNjEwLCJpYXQiOjE3NzIwNzAwMTAsImVtYWlsIjoidXNlcnRlc3QyQGdtYWlsLmNvbSIsInBob25lIjoiIiwiYXBwX21ldGFkYXRhIjp7InByb3ZpZGVyIjoiZW1haWwiLCJwcm92aWRlcnMiOlsiZW1haWwiXX0sInVzZXJfbWV0YWRhdGEiOnsiZW1haWxfdmVyaWZpZWQiOnRydWV9LCJyb2xlIjoiYXV0aGVudGljYXRlZCIsImFhbCI6ImFhbDEiLCJhbXIiOlt7Im1ldGhvZCI6InBhc3N3b3JkIiwidGltZXN0YW1wIjoxNzcyMDcwMDEwfV0sInNlc3Npb25faWQiOiI4ZDBjYjMwYy1iYmI1LTRjZWUtYjAxNS02ZTUxNWY4Y2YwNDQiLCJpc19hbm9ueW1vdXMiOmZhbHNlfQ._KcJJcQDfR21CZnrAh_Vy0zi5rs_4NXo92RfxLFIqov3bEpyxbkkUZUOjAn-iootSXak47fZ1rSDBveZnk5b6Q",
    "user3": "eyJhbGciOiJFUzI1NiIsImtpZCI6IjRkYjg1ZGY5LTc5NDItNGFjMy04MzQzLWU2MjY4ZGVlYmMwNyIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJodHRwczovL3BteXN5dG11c3F1bmtlbnh6b3FtLnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiIyODY1MjEzNS04ZDFkLTQwZjktYTY3MS0zYzhhYzlhNDI4ODgiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzcyMDczNjM5LCJpYXQiOjE3NzIwNzAwMzksImVtYWlsIjoidXNlcnRlc3QzQGdtYWlsLmNvbSIsInBob25lIjoiIiwiYXBwX21ldGFkYXRhIjp7InByb3ZpZGVyIjoiZW1haWwiLCJwcm92aWRlcnMiOlsiZW1haWwiXX0sInVzZXJfbWV0YWRhdGEiOnsiZW1haWxfdmVyaWZpZWQiOnRydWV9LCJyb2xlIjoiYXV0aGVudGljYXRlZCIsImFhbCI6ImFhbDEiLCJhbXIiOlt7Im1ldGhvZCI6InBhc3N3b3JkIiwidGltZXN0YW1wIjoxNzcyMDcwMDM5fV0sInNlc3Npb25faWQiOiIxZDEzYjI3Zi05YjY3LTQ5MjMtYTA2OC02MDNjNGEzMWMzZmEiLCJpc19hbm9ueW1vdXMiOmZhbHNlfQ.CWOMJzk8L1MlumwoJQy_oc9FxKIe176RBldwRbvxcjLrpQN8RfGABPDQ8hrced0t996-ZFW49Tl2TrsN-4GfAQ",
}

# Volumen por usuario
NUM_TASKS = 20
NUM_NOTES = 20
NUM_EVENTS = 20
NUM_TAGS = 5
NUM_RELATIONS = 5    # vinculaciones por tipo (task-note, task-event, note-event)
NUM_TAG_ASSIGNS = 10 # asignaciones de tags por entidad tipo
NUM_READS = 5        # lecturas individuales por entidad tipo
NUM_UPDATES = 5      # updates parciales por entidad tipo

# ─── Contadores globales ──────────────────────────────────────────────────────
stats = {"ok": 0, "fail": 0, "errors": []}
request_log: list[dict] = []  # Registro detallado de cada request para el CSV
current_phase = ""             # Fase activa (se actualiza en main)

# ─── Almacén de IDs creados ───────────────────────────────────────────────────
# Estructura: { "user1": { "tasks": [], "notes": [], "events": [], "tags": [] } }
created = {u: {"tasks": [], "notes": [], "events": [], "tags": []} for u in TOKENS}

# ─── Datos de prueba ──────────────────────────────────────────────────────────
TAG_COLORS = ["#FF5733", "#33FF57", "#3357FF", "#F1C40F", "#9B59B6"]
TAG_NAMES = {
    "user1": ["Trabajo", "Personal", "Urgente", "Estudio", "Salud"],
    "user2": ["Proyecto", "Casa", "Deporte", "Lectura", "Finanzas"],
    "user3": ["Coding", "Música", "Viajes", "Comida", "Social"],
}
PRIORITIES = ["baja", "media", "alta"]


# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS ASYNC
# ═══════════════════════════════════════════════════════════════════════════════

def headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def _find_user(token: str) -> str:
    """Identifica el nombre del usuario dado su token."""
    for u, t in TOKENS.items():
        if t == token:
            return u
    return "unknown"


async def post(session: aiohttp.ClientSession, url: str, token: str, data: dict) -> dict | None:
    """POST genérico con tracking de métricas."""
    t0 = time.time()
    user = _find_user(token)
    try:
        async with session.post(url, json=data, headers=headers(token)) as resp:
            elapsed = time.time() - t0
            body = await resp.json()
            ok = resp.status in (200, 201)
            if ok:
                stats["ok"] += 1
            else:
                stats["fail"] += 1
                stats["errors"].append({"method": "POST", "url": url, "status": resp.status, "body": body})
            request_log.append({"phase": current_phase, "user": user, "method": "POST", "url": url, "status": resp.status, "duration_ms": round(elapsed * 1000), "ok": ok})
            return body if ok else None
    except Exception as e:
        elapsed = time.time() - t0
        stats["fail"] += 1
        stats["errors"].append({"method": "POST", "url": url, "error": str(e)})
        request_log.append({"phase": current_phase, "user": user, "method": "POST", "url": url, "status": "ERR", "duration_ms": round(elapsed * 1000), "ok": False})
        return None


async def get(session: aiohttp.ClientSession, url: str, token: str) -> dict | list | None:
    """GET genérico con tracking de métricas."""
    t0 = time.time()
    user = _find_user(token)
    try:
        async with session.get(url, headers=headers(token)) as resp:
            elapsed = time.time() - t0
            body = await resp.json()
            ok = resp.status == 200
            if ok:
                stats["ok"] += 1
            else:
                stats["fail"] += 1
                stats["errors"].append({"method": "GET", "url": url, "status": resp.status, "body": body})
            request_log.append({"phase": current_phase, "user": user, "method": "GET", "url": url, "status": resp.status, "duration_ms": round(elapsed * 1000), "ok": ok})
            return body if ok else None
    except Exception as e:
        elapsed = time.time() - t0
        stats["fail"] += 1
        stats["errors"].append({"method": "GET", "url": url, "error": str(e)})
        request_log.append({"phase": current_phase, "user": user, "method": "GET", "url": url, "status": "ERR", "duration_ms": round(elapsed * 1000), "ok": False})
        return None


async def patch(session: aiohttp.ClientSession, url: str, token: str, data: dict) -> dict | None:
    """PATCH genérico con tracking de métricas."""
    t0 = time.time()
    user = _find_user(token)
    try:
        async with session.patch(url, json=data, headers=headers(token)) as resp:
            elapsed = time.time() - t0
            body = await resp.json()
            ok = resp.status == 200
            if ok:
                stats["ok"] += 1
            else:
                stats["fail"] += 1
                stats["errors"].append({"method": "PATCH", "url": url, "status": resp.status, "body": body})
            request_log.append({"phase": current_phase, "user": user, "method": "PATCH", "url": url, "status": resp.status, "duration_ms": round(elapsed * 1000), "ok": ok})
            return body if ok else None
    except Exception as e:
        elapsed = time.time() - t0
        stats["fail"] += 1
        stats["errors"].append({"method": "PATCH", "url": url, "error": str(e)})
        request_log.append({"phase": current_phase, "user": user, "method": "PATCH", "url": url, "status": "ERR", "duration_ms": round(elapsed * 1000), "ok": False})
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# FASE 1 — CREAR TAGS
# ═══════════════════════════════════════════════════════════════════════════════

async def phase_1_tags(session: aiohttp.ClientSession):
    """Cada usuario crea 5 etiquetas únicas."""
    tasks = []
    for user, token in TOKENS.items():
        for i in range(NUM_TAGS):
            data = {"name": TAG_NAMES[user][i], "color": TAG_COLORS[i]}
            tasks.append(_create_tag(session, user, token, data))
    await asyncio.gather(*tasks)


async def _create_tag(session, user, token, data):
    result = await post(session, f"{BASE_URL}/tags/", token, data)
    if result and "id" in result:
        created[user]["tags"].append(result["id"])


# ═══════════════════════════════════════════════════════════════════════════════
# FASE 2 — CREAR ENTIDADES
# ═══════════════════════════════════════════════════════════════════════════════

async def phase_2_entities(session: aiohttp.ClientSession):
    """Cada usuario crea 20 tasks, 20 notes, 20 events en paralelo."""
    all_coros = []
    for user, token in TOKENS.items():
        # Tareas
        for i in range(NUM_TASKS):
            base_date = datetime(2026, 3, 1) + timedelta(days=i)
            has_reminder = i % 3 == 0
            data = {
                "title": f"[{user}] Tarea #{i+1}",
                "description": f"Descripción de prueba para tarea {i+1} del {user}",
                "due_date": base_date.isoformat() + "Z",
                "priority": PRIORITIES[i % 3],
                "is_completed": False,
            }
            if has_reminder:
                data["reminders"] = [{"unit": "hours", "value": random.choice([1, 2, 24])}]
            all_coros.append(_create_entity(session, user, token, "tasks", data))

        # Notas
        for i in range(NUM_NOTES):
            data = {
                "title": f"[{user}] Nota #{i+1}",
                "content": f"Contenido de prueba para nota {i+1}. " * 3,
            }
            all_coros.append(_create_entity(session, user, token, "notes", data))

        # Eventos
        for i in range(NUM_EVENTS):
            start = datetime(2026, 3, 1, 9, 0) + timedelta(days=i, hours=i % 8)
            end = start + timedelta(hours=random.choice([1, 2, 3]))
            has_reminder = i % 4 == 0
            data = {
                "title": f"[{user}] Evento #{i+1}",
                "description": f"Evento de prueba {i+1}",
                "start_time": start.isoformat() + "Z",
                "end_time": end.isoformat() + "Z",
                "location": f"Sala {chr(65 + i % 5)}",
                "is_all_day": False,
            }
            if has_reminder:
                data["reminders"] = [{"unit": "minutes", "value": random.choice([15, 30, 60])}]
            all_coros.append(_create_entity(session, user, token, "events", data))

    await asyncio.gather(*all_coros)


async def _create_entity(session, user, token, entity_type, data):
    result = await post(session, f"{BASE_URL}/{entity_type}/", token, data)
    if result and "id" in result:
        created[user][entity_type].append(result["id"])


# ═══════════════════════════════════════════════════════════════════════════════
# FASE 3 — VINCULAR ENTIDADES
# ═══════════════════════════════════════════════════════════════════════════════

async def phase_3_relations(session: aiohttp.ClientSession):
    """Vincula entidades entre sí y asigna tags."""
    all_coros = []
    for user, token in TOKENS.items():
        t = created[user]["tasks"]
        n = created[user]["notes"]
        e = created[user]["events"]
        tags = created[user]["tags"]

        if len(t) < NUM_RELATIONS or len(n) < NUM_RELATIONS or len(e) < NUM_RELATIONS:
            print(f"  ⚠️  {user}: IDs insuficientes para vincular (tasks={len(t)}, notes={len(n)}, events={len(e)})")
            continue

        # Relaciones cruzadas via /api/relations
        for i in range(NUM_RELATIONS):
            all_coros.append(post(session, f"{BASE_URL}/relations/task-note", token, {"task_id": t[i], "note_id": n[i]}))
            all_coros.append(post(session, f"{BASE_URL}/relations/task-event", token, {"task_id": t[i], "event_id": e[i]}))
            all_coros.append(post(session, f"{BASE_URL}/relations/note-event", token, {"note_id": n[i], "event_id": e[i]}))

        # Asignar tags a entidades
        if tags:
            for i in range(min(NUM_TAG_ASSIGNS, len(t))):
                tag_id = tags[i % len(tags)]
                all_coros.append(post(session, f"{BASE_URL}/tasks/{t[i]}/tags", token, {"tag_id": tag_id}))
            for i in range(min(NUM_TAG_ASSIGNS, len(n))):
                tag_id = tags[i % len(tags)]
                all_coros.append(post(session, f"{BASE_URL}/notes/{n[i]}/tags", token, {"tag_id": tag_id}))
            for i in range(min(NUM_TAG_ASSIGNS, len(e))):
                tag_id = tags[i % len(tags)]
                all_coros.append(post(session, f"{BASE_URL}/events/{e[i]}/tags", token, {"tag_id": tag_id}))

    await asyncio.gather(*all_coros)


# ═══════════════════════════════════════════════════════════════════════════════
# FASE 4 — CONSULTAS MASIVAS
# ═══════════════════════════════════════════════════════════════════════════════

async def phase_4_reads(session: aiohttp.ClientSession):
    """Lecturas concurrentes: listados, detalles y /related."""
    all_coros = []
    for user, token in TOKENS.items():
        # Listados generales
        all_coros.append(get(session, f"{BASE_URL}/tasks/", token))
        all_coros.append(get(session, f"{BASE_URL}/notes/", token))
        all_coros.append(get(session, f"{BASE_URL}/events/", token))
        all_coros.append(get(session, f"{BASE_URL}/tags/", token))

        # Detalle + /related por entidad
        for entity_type in ["tasks", "notes", "events"]:
            ids = created[user][entity_type]
            sample = ids[:NUM_READS] if len(ids) >= NUM_READS else ids
            for eid in sample:
                all_coros.append(get(session, f"{BASE_URL}/{entity_type}/{eid}", token))
                all_coros.append(get(session, f"{BASE_URL}/{entity_type}/{eid}/related", token))

    await asyncio.gather(*all_coros)


# ═══════════════════════════════════════════════════════════════════════════════
# FASE 5 — UPDATES PARCIALES
# ═══════════════════════════════════════════════════════════════════════════════

async def phase_5_updates(session: aiohttp.ClientSession):
    """Cada usuario actualiza 5 tasks, 5 notes y 5 events."""
    all_coros = []
    for user, token in TOKENS.items():
        # Actualizar tareas
        for i, tid in enumerate(created[user]["tasks"][:NUM_UPDATES]):
            data = {"title": f"[{user}] Tarea #{i+1} (actualizada)", "priority": PRIORITIES[(i + 1) % 3]}
            all_coros.append(patch(session, f"{BASE_URL}/tasks/{tid}", token, data))

        # Actualizar notas
        for i, nid in enumerate(created[user]["notes"][:NUM_UPDATES]):
            data = {"title": f"[{user}] Nota #{i+1} (actualizada)", "content": "Contenido editado en prueba de estrés."}
            all_coros.append(patch(session, f"{BASE_URL}/notes/{nid}", token, data))

        # Actualizar eventos
        for i, eid in enumerate(created[user]["events"][:NUM_UPDATES]):
            new_start = datetime(2026, 4, 1, 10, 0) + timedelta(days=i)
            new_end = new_start + timedelta(hours=2)
            data = {
                "title": f"[{user}] Evento #{i+1} (actualizado)",
                "start_time": new_start.isoformat() + "Z",
                "end_time": new_end.isoformat() + "Z",
            }
            all_coros.append(patch(session, f"{BASE_URL}/events/{eid}", token, data))

    await asyncio.gather(*all_coros)


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

async def main():
    print("═" * 50)
    print("  PRUEBAS DE ESTRÉS — OrganizaT API")
    print(f"  URL: {BASE_URL}")
    print(f"  Usuarios: {len(TOKENS)}")
    print("═" * 50)

    # Validar que los tokens no sean los placeholders
    for user, token in TOKENS.items():
        if "PEGAR_JWT" in token:
            print(f"\n  ❌ ERROR: Reemplaza el JWT placeholder de '{user}' antes de ejecutar.")
            return

    total_start = time.time()
    phase_times = {}

    # Timeout generoso para Vercel (funciones serverless pueden tardar)
    timeout = aiohttp.ClientTimeout(total=120)
    async with aiohttp.ClientSession(timeout=timeout) as session:

        # Fase 1
        print("\n▶ Fase 1: Creando tags...")
        current_phase = "1_tags"
        t0 = time.time()
        await phase_1_tags(session)
        phase_times["Tags"] = time.time() - t0
        _print_created_summary()

        # Fase 2
        print("\n▶ Fase 2: Creando entidades (tasks, notes, events)...")
        current_phase = "2_entidades"
        t0 = time.time()
        await phase_2_entities(session)
        phase_times["Entidades"] = time.time() - t0
        _print_created_summary()

        # Fase 3
        print("\n▶ Fase 3: Vinculando entidades y asignando tags...")
        current_phase = "3_relaciones"
        t0 = time.time()
        await phase_3_relations(session)
        phase_times["Relaciones"] = time.time() - t0

        # Fase 4
        print("\n▶ Fase 4: Consultas masivas (list + detail + related)...")
        current_phase = "4_lecturas"
        t0 = time.time()
        await phase_4_reads(session)
        phase_times["Lecturas"] = time.time() - t0

        # Fase 5
        print("\n▶ Fase 5: Updates parciales...")
        current_phase = "5_updates"
        t0 = time.time()
        await phase_5_updates(session)
        phase_times["Updates"] = time.time() - t0

    total_time = time.time() - total_start

    # Reporte final
    print("\n" + "═" * 50)
    print("  REPORTE DE PRUEBAS DE ESTRÉS")
    print("═" * 50)
    for phase_name, elapsed in phase_times.items():
        print(f"  {phase_name:<15} {elapsed:>6.1f}s")
    print("─" * 50)
    total_requests = stats["ok"] + stats["fail"]
    print(f"  {'TOTAL':<15} {total_time:>6.1f}s  |  {stats['ok']}/{total_requests} OK  |  {stats['fail']} errores")
    print("═" * 50)

    if stats["errors"]:
        print(f"\n  ⚠️  Primeros 10 errores:")
        for err in stats["errors"][:10]:
            print(f"    {err}")

    # Veredicto
    if total_time < 120 and stats["fail"] == 0:
        print("\n  ✅ RESULTADO: PASÓ — sin errores y dentro del tiempo límite.")
    elif total_time >= 120:
        print(f"\n  ❌ RESULTADO: FALLÓ — excedió los 120 segundos ({total_time:.1f}s).")
    else:
        print(f"\n  ⚠️  RESULTADO: PARCIAL — {stats['fail']} errores detectados.")

    # Exportar CSV
    _export_csv(phase_times, total_time)


def _print_created_summary():
    """Imprime resumen de IDs creados por usuario."""
    for user in TOKENS:
        c = created[user]
        print(f"    {user}: {len(c['tags'])} tags, {len(c['tasks'])} tasks, {len(c['notes'])} notes, {len(c['events'])} events")


def _export_csv(phase_times: dict, total_time: float):
    """Genera un CSV con el detalle de cada request y una hoja de resumen."""
    output_dir = os.path.dirname(os.path.abspath(__file__))
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # --- CSV detallado: cada request ---
    detail_path = os.path.join(output_dir, f"stress_detail_{timestamp}.csv")
    with open(detail_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["phase", "user", "method", "url", "status", "duration_ms", "ok"])
        writer.writeheader()
        writer.writerows(request_log)

    # --- CSV resumen ---
    summary_path = os.path.join(output_dir, f"stress_summary_{timestamp}.csv")
    with open(summary_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Sección", "Métrica", "Valor"])

        # Resumen general
        total_requests = stats["ok"] + stats["fail"]
        writer.writerow(["General", "URL Base", BASE_URL])
        writer.writerow(["General", "Usuarios", len(TOKENS)])
        writer.writerow(["General", "Total Requests", total_requests])
        writer.writerow(["General", "Exitosos", stats["ok"]])
        writer.writerow(["General", "Fallidos", stats["fail"]])
        writer.writerow(["General", "Tiempo Total (s)", round(total_time, 2)])
        writer.writerow(["General", "Requests/seg", round(total_requests / total_time, 2) if total_time > 0 else 0])
        writer.writerow([])

        # Tiempos por fase
        for phase_name, elapsed in phase_times.items():
            writer.writerow(["Fase", phase_name, f"{elapsed:.2f}s"])
        writer.writerow([])

        # Latencia por fase (promedio y p95)
        writer.writerow(["Latencia", "Fase", "Promedio (ms)", "P95 (ms)", "Max (ms)"])
        # Reagrupar request_log por fase
        phases = {}
        for r in request_log:
            phases.setdefault(r["phase"], []).append(r["duration_ms"])
        for ph, durations in phases.items():
            durations_sorted = sorted(durations)
            avg = round(sum(durations_sorted) / len(durations_sorted))
            p95 = durations_sorted[int(len(durations_sorted) * 0.95)] if durations_sorted else 0
            mx = durations_sorted[-1] if durations_sorted else 0
            writer.writerow(["", ph, avg, p95, mx])
        writer.writerow([])

        # Entidades creadas por usuario
        writer.writerow(["Entidades", "Usuario", "Tags", "Tasks", "Notes", "Events"])
        for user in TOKENS:
            c = created[user]
            writer.writerow(["", user, len(c["tags"]), len(c["tasks"]), len(c["notes"]), len(c["events"])])
        writer.writerow([])

        # Errores (primeros 20)
        if stats["errors"]:
            writer.writerow(["Errores", "Método", "URL", "Status/Error"])
            for err in stats["errors"][:20]:
                method = err.get("method", "")
                url = err.get("url", "")
                status = err.get("status", err.get("error", ""))
                writer.writerow(["", method, url, status])

    print(f"\n  📄 CSV detallado:  {detail_path}")
    print(f"  📄 CSV resumen:    {summary_path}")


if __name__ == "__main__":
    asyncio.run(main())
