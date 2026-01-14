from fastapi import FastAPI

app = FastAPI()

@app.get("/", tags=["Health"])
def read_root():
    return {"message": "Hola Mundo desde FastAPI en Vercel"}

@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}
