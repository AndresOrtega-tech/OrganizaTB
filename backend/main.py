from fastapi import FastAPI
from database import supabase

app = FastAPI()

@app.get("/", tags=["Health"])
def read_root():
    return {"message": "Hola Mundo desde FastAPI en Vercel"}

@app.get("/tables", tags=["Health"])
def list_tables():
    try:
        # Intentamos llamar a una función RPC 'get_tables'
        response = supabase.rpc('get_tables', {}).execute()
        return {"tables": response.data}
    except Exception as e:
        return {
            "status": "error",
            "message": "No se pudieron listar las tablas. Asegúrate de haber creado la función RPC en Supabase.",
            "details": str(e),
            "solution": "Ejecuta este SQL en el Editor SQL de Supabase:",
            "sql_command": "create or replace function get_tables() returns json language sql as $$ select json_agg(table_name) from information_schema.tables where table_schema = 'public'; $$;"
        }
