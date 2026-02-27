"""
Prueba de límites (ESCRITURAS) — OrganizaT API
Escala la concurrencia de POSTs (crear tareas) hasta encontrar el punto de quiebre.
⚠️ CREA DATOS REALES en BD. Limpiar después si es necesario.
Uso: python tests/pruebas_limite_write_v1.py
"""

import asyncio
import aiohttp
import time
import csv
import os
import random
from datetime import datetime, timedelta

# ─── Configuración ────────────────────────────────────────────────────────────
BASE_URL = "https://api-organiza-tb.vercel.app/api"

TOKENS = [
    "eyJhbGciOiJFUzI1NiIsImtpZCI6IjRkYjg1ZGY5LTc5NDItNGFjMy04MzQzLWU2MjY4ZGVlYmMwNyIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJodHRwczovL3BteXN5dG11c3F1bmtlbnh6b3FtLnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiIzOWVkMjAxZS1hN2I2LTQ0NGYtODA3Ny04ODBjMWI0NTc3ZWEiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzcyMjExOTQ0LCJpYXQiOjE3NzIyMDgzNDQsImVtYWlsIjoidXNlcnRlc3Q0QGdtYWlsLmNvbSIsInBob25lIjoiIiwiYXBwX21ldGFkYXRhIjp7InByb3ZpZGVyIjoiZW1haWwiLCJwcm92aWRlcnMiOlsiZW1haWwiXX0sInVzZXJfbWV0YWRhdGEiOnsiZW1haWxfdmVyaWZpZWQiOnRydWV9LCJyb2xlIjoiYXV0aGVudGljYXRlZCIsImFhbCI6ImFhbDEiLCJhbXIiOlt7Im1ldGhvZCI6InBhc3N3b3JkIiwidGltZXN0YW1wIjoxNzcyMjA4MzQ0fV0sInNlc3Npb25faWQiOiJlNGUyMDM0MC0wYWE5LTQxNWQtYWNhZS0xMDI4NGNiOWQxOWUiLCJpc19hbm9ueW1vdXMiOmZhbHNlfQ.xqxPkYP32YqaIzKO1xnoOnEHKcBBeXJTS1rc79pMxvDKmSPl3yp5-L4PoGTZN9IUpnw2fejoV1eNw1OMlgPGxQ",
    "eyJhbGciOiJFUzI1NiIsImtpZCI6IjRkYjg1ZGY5LTc5NDItNGFjMy04MzQzLWU2MjY4ZGVlYmMwNyIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJodHRwczovL3BteXN5dG11c3F1bmtlbnh6b3FtLnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiI3MzdiNTMwYy05ODBhLTQwYWEtYTZhZC1iMzM0ZGRkNmRjYmQiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzcyMjExOTY4LCJpYXQiOjE3NzIyMDgzNjgsImVtYWlsIjoidXNlcnRlc3QyQGdtYWlsLmNvbSIsInBob25lIjoiIiwiYXBwX21ldGFkYXRhIjp7InByb3ZpZGVyIjoiZW1haWwiLCJwcm92aWRlcnMiOlsiZW1haWwiXX0sInVzZXJfbWV0YWRhdGEiOnsiZW1haWxfdmVyaWZpZWQiOnRydWV9LCJyb2xlIjoiYXV0aGVudGljYXRlZCIsImFhbCI6ImFhbDEiLCJhbXIiOlt7Im1ldGhvZCI6InBhc3N3b3JkIiwidGltZXN0YW1wIjoxNzcyMjA4MzY4fV0sInNlc3Npb25faWQiOiIxY2ExNWFkYS1jNjNjLTQwZGUtYjg2NS1kZjY2OWRhYjU4NzAiLCJpc19hbm9ueW1vdXMiOmZhbHNlfQ.IrftKdEkHDHIPSdTirZNoaIp1bOhKRvKD7AZ-r5f4pri-r5j7tvBsWdWWJSIX3qhpEuKCCms2T3rfqzFl2lG3A",
    "eyJhbGciOiJFUzI1NiIsImtpZCI6IjRkYjg1ZGY5LTc5NDItNGFjMy04MzQzLWU2MjY4ZGVlYmMwNyIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJodHRwczovL3BteXN5dG11c3F1bmtlbnh6b3FtLnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiIyODY1MjEzNS04ZDFkLTQwZjktYTY3MS0zYzhhYzlhNDI4ODgiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzcyMjExOTk1LCJpYXQiOjE3NzIyMDgzOTUsImVtYWlsIjoidXNlcnRlc3QzQGdtYWlsLmNvbSIsInBob25lIjoiIiwiYXBwX21ldGFkYXRhIjp7InByb3ZpZGVyIjoiZW1haWwiLCJwcm92aWRlcnMiOlsiZW1haWwiXX0sInVzZXJfbWV0YWRhdGEiOnsiZW1haWxfdmVyaWZpZWQiOnRydWV9LCJyb2xlIjoiYXV0aGVudGljYXRlZCIsImFhbCI6ImFhbDEiLCJhbXIiOlt7Im1ldGhvZCI6InBhc3N3b3JkIiwidGltZXN0YW1wIjoxNzcyMjA4Mzk1fV0sInNlc3Npb25faWQiOiI4ZGI5NTI4My00Nzg3LTQ3NzMtOGEwMS1hYjJlY2Q2NDNkODkiLCJpc19hbm9ueW1vdXMiOmZhbHNlfQ.de6DZ0NXBBTflGYoso6RpjcbCaXbOYoYKiaciyRbDEOhzATjY2BACRYaJEDg9QeLvPNllwYstsTa51oa7lnqOg",
]

# Niveles de concurrencia (rampa) — escrituras son más pesadas, escalamos más suave
CONCURRENCY_LEVELS = [500, 750, 1000, 1500, 2000, 3000, 5000]

PRIORITIES = ["baja", "media", "alta"]

# Umbral de error para detener (50%)
ERROR_THRESHOLD = 0.50

# Pausa entre rondas (segundos)
COOLDOWN_SECONDS = 8

# Conteo de tareas creadas (para ver cuánto limpiar después)
total_created = 0


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLE WRITE REQUEST
# ═══════════════════════════════════════════════════════════════════════════════

def _make_task_payload(level: int, index: int) -> dict:
    """Genera un payload de tarea único para evitar colisiones."""
    base_date = datetime(2026, 6, 1) + timedelta(days=index % 30, hours=index % 24)
    return {
        "title": f"[stress-write] L{level}-R{index}-{int(time.time()*1000) % 100000}",
        "description": f"Tarea de prueba de límite de escritura. Nivel={level}, idx={index}",
        "due_date": base_date.isoformat() + "Z",
        "priority": PRIORITIES[index % 3],
        "is_completed": False,
    }


async def single_write(session: aiohttp.ClientSession, token: str, level: int, index: int) -> dict:
    """Ejecuta un POST /tasks/ y retorna métricas."""
    global total_created
    url = f"{BASE_URL}/tasks/"
    payload = _make_task_payload(level, index)
    t0 = time.time()
    try:
        async with session.post(url, json=payload, headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"}) as resp:
            elapsed_ms = round((time.time() - t0) * 1000)
            try:
                await resp.read()
            except Exception:
                pass
            ok = resp.status in (200, 201)
            if ok:
                total_created += 1
            return {"status": resp.status, "duration_ms": elapsed_ms, "ok": ok, "error": None}
    except asyncio.TimeoutError:
        elapsed_ms = round((time.time() - t0) * 1000)
        return {"status": "TIMEOUT", "duration_ms": elapsed_ms, "ok": False, "error": "timeout"}
    except Exception as e:
        elapsed_ms = round((time.time() - t0) * 1000)
        return {"status": "ERR", "duration_ms": elapsed_ms, "ok": False, "error": str(e)[:100]}


# ═══════════════════════════════════════════════════════════════════════════════
# RONDA
# ═══════════════════════════════════════════════════════════════════════════════

async def run_round(session: aiohttp.ClientSession, concurrency: int) -> dict:
    """Lanza `concurrency` POSTs simultáneos distribuyendo entre los 3 tokens."""
    coros = []
    for i in range(concurrency):
        token = TOKENS[i % len(TOKENS)]
        coros.append(single_write(session, token, concurrency, i))

    results = await asyncio.gather(*coros)

    ok_count = sum(1 for r in results if r["ok"])
    fail_count = concurrency - ok_count
    durations = sorted([r["duration_ms"] for r in results])

    avg_ms = round(sum(durations) / len(durations)) if durations else 0
    p50 = durations[int(len(durations) * 0.50)] if durations else 0
    p95 = durations[int(len(durations) * 0.95)] if durations else 0
    p99 = durations[int(len(durations) * 0.99)] if durations else 0
    max_ms = durations[-1] if durations else 0
    min_ms = durations[0] if durations else 0

    error_types = {}
    for r in results:
        if not r["ok"]:
            key = str(r["status"])
            error_types[key] = error_types.get(key, 0) + 1

    return {
        "concurrency": concurrency, "total": concurrency,
        "ok": ok_count, "fail": fail_count,
        "ok_pct": round((ok_count / concurrency) * 100, 1),
        "avg_ms": avg_ms, "min_ms": min_ms, "p50_ms": p50,
        "p95_ms": p95, "p99_ms": p99, "max_ms": max_ms,
        "error_types": error_types, "raw_results": results,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

async def main():
    print("═" * 65)
    print("  PRUEBA DE LÍMITES (ESCRITURA) — OrganizaT API")
    print(f"  URL: {BASE_URL}")
    print(f"  Endpoint: POST /tasks/")
    print(f"  Tokens: {len(TOKENS)} usuarios")
    print(f"  Niveles: {CONCURRENCY_LEVELS}")
    print(f"  Umbral de error: {int(ERROR_THRESHOLD * 100)}%")
    print("═" * 65)

    timeout = aiohttp.ClientTimeout(total=60)
    connector = aiohttp.TCPConnector(limit=0, limit_per_host=0)

    rounds: list[dict] = []
    limit_found = None

    async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:

        # Warmup
        print("\n  🔥 Warmup (1 POST)...")
        await single_write(session, TOKENS[0], 0, 0)
        await asyncio.sleep(2)

        for level in CONCURRENCY_LEVELS:
            print(f"\n▶ Ronda: {level} POSTs simultáneos...")
            t0 = time.time()
            result = await run_round(session, level)
            elapsed = time.time() - t0
            result["round_time_s"] = round(elapsed, 2)
            rounds.append(result)

            err_str = f"  Errores: {result['error_types']}" if result["error_types"] else ""
            print(f"    ✓ {result['ok']}/{result['total']} OK ({result['ok_pct']}%)  "
                  f"| Avg: {result['avg_ms']}ms  P95: {result['p95_ms']}ms  Max: {result['max_ms']}ms  "
                  f"| Ronda: {result['round_time_s']}s")
            if err_str:
                print(f"    {err_str}")

            error_rate = result["fail"] / result["total"]
            if error_rate >= ERROR_THRESHOLD:
                limit_found = rounds[-2]["concurrency"] if len(rounds) > 1 else 0
                print(f"\n  🛑 Tasa de error ({error_rate:.0%}) superó el umbral.")
                print(f"     Último nivel estable: {limit_found} POSTs simultáneos.")
                break

            if level != CONCURRENCY_LEVELS[-1]:
                print(f"    ⏳ Cooldown {COOLDOWN_SECONDS}s...")
                await asyncio.sleep(COOLDOWN_SECONDS)

    if limit_found is None:
        limit_found = CONCURRENCY_LEVELS[-1]
        print(f"\n  🚀 La API soportó todos los niveles de escritura.")

    # Reporte
    print("\n" + "═" * 85)
    print("  REPORTE DE LÍMITES (ESCRITURA)")
    print("═" * 85)
    print(f"  {'Concurrencia':>12} | {'OK%':>5} | {'Avg(ms)':>8} | {'P50(ms)':>8} | {'P95(ms)':>8} | {'Max(ms)':>8} | {'Errores':>7} | {'Tiempo':>7}")
    print("─" * 85)
    for r in rounds:
        print(f"  {r['concurrency']:>12} | {r['ok_pct']:>4}% | {r['avg_ms']:>8} | {r['p50_ms']:>8} | {r['p95_ms']:>8} | {r['max_ms']:>8} | {r['fail']:>7} | {r['round_time_s']:>6}s")
    print("═" * 85)
    print(f"\n  📊 LÍMITE ESTIMADO (ESCRITURA): {limit_found} POSTs simultáneos")
    print(f"  📦 Total tareas creadas en BD: {total_created}")

    _export_csv(rounds, limit_found)


def _export_csv(rounds: list[dict], limit_found: int):
    """Genera CSVs con resultados."""
    output_dir = os.path.dirname(os.path.abspath(__file__))
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    summary_path = os.path.join(output_dir, f"limit_write_summary_{timestamp}.csv")
    with open(summary_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["concurrency", "total", "ok", "fail", "ok_pct", "avg_ms", "min_ms", "p50_ms", "p95_ms", "p99_ms", "max_ms", "round_time_s", "error_types"])
        for r in rounds:
            writer.writerow([
                r["concurrency"], r["total"], r["ok"], r["fail"], r["ok_pct"],
                r["avg_ms"], r["min_ms"], r["p50_ms"], r["p95_ms"], r["p99_ms"], r["max_ms"],
                r["round_time_s"], str(r["error_types"]) if r["error_types"] else ""
            ])
        writer.writerow([])
        writer.writerow(["LIMITE_ESTIMADO", limit_found])
        writer.writerow(["TOTAL_TAREAS_CREADAS", total_created])

    detail_path = os.path.join(output_dir, f"limit_write_detail_{timestamp}.csv")
    with open(detail_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["concurrency_level", "request_index", "status", "duration_ms", "ok", "error"])
        for r in rounds:
            for i, req in enumerate(r["raw_results"]):
                writer.writerow([r["concurrency"], i, req["status"], req["duration_ms"], req["ok"], req.get("error", "")])

    print(f"\n  📄 CSV resumen:    {summary_path}")
    print(f"  📄 CSV detallado:  {detail_path}")


if __name__ == "__main__":
    asyncio.run(main())
