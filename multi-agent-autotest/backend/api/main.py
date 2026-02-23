from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from api.routes import router
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

app = FastAPI(
    title="Multi Agent AutoTest",
    description="Geração automática de testes pytest com múltiplos agentes de IA",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# Serve os reports HTML do coverage como arquivos estáticos
REPORTS_DIR = Path(__file__).parent.parent / "reports"
REPORTS_DIR.mkdir(exist_ok=True)
app.mount("/reports", StaticFiles(directory=str(REPORTS_DIR)), name="reports")

app.include_router(router, prefix="/api")