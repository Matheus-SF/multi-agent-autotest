from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from agents.graph import agent_graph
from pathlib import Path
import os

router = APIRouter()


@router.get("/health")
def health():
    """
    Endpoint simples para o frontend verificar se o backend está vivo.
    """
    return {"status": "ok"}


@router.post("/analyze")
async def analyze(
    files: list[UploadFile] = File(...),
    threshold: float = Form(default=80.0),
    max_iterations: int = Form(default=5)
):
    """
    Endpoint principal — recebe os arquivos .py do usuário,
    dispara o grafo de agentes e retorna o relatório final.

    Args:
        files: lista de arquivos .py enviados pelo React
        threshold: meta de cobertura (padrão 80%)
        max_iterations: limite de iterações do loop (padrão 5)
    """

    # Valida se todos os arquivos são .py
    for file in files:
        if not file.filename.endswith(".py"):
            raise HTTPException(
                status_code=400,
                detail=f"Arquivo '{file.filename}' não é um arquivo Python válido."
            )

    # Lê o conteúdo de cada arquivo enviado
    files_content: dict[str, str] = {}
    for file in files:
        content = await file.read()
        files_content[file.filename] = content.decode("utf-8")

    # Monta o state inicial do grafo
    initial_state = {
        "files": files_content,
        "threshold": threshold,
        "max_iterations": max_iterations,
        "iteration": 1,
        "should_iterate": True,
        "review_reason": "",
        "analysis": {},
        "generated_tests": "",
        "coverage_pct": 0.0,
        "uncovered_lines": {},
        "report": {}
    }

    try:
        # Invoca o grafo — isso é bloqueante até o loop encerrar
        final_state = await agent_graph.ainvoke(initial_state)
        return JSONResponse(content=final_state["report"])

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))