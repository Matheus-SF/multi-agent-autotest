from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from prompts.loader import render
import re
import os


def _corrigir_imports(code: str) -> str:
    """
    Detecta uso de módulos comuns e injeta imports faltantes.
    Evita NameError causados pelo LLM que usa módulos sem importar.
    """
    imports_necessarios = {
        "subprocess.":          "import subprocess",
        "ET.":                  "import xml.etree.ElementTree as ET",
        "Path(":                "from pathlib import Path",
        "MagicMock":            "from unittest.mock import patch, MagicMock",
        "patch(":               "from unittest.mock import patch, MagicMock",
        "pytest.raises":        "import pytest",
        "pytest.fixture":       "import pytest",
    }

    linhas = code.split("\n")
    imports_existentes = "\n".join(
        l for l in linhas
        if l.startswith("import") or l.startswith("from")
    )

    para_adicionar = []
    for token, import_stmt in imports_necessarios.items():
        if token in code and import_stmt not in imports_existentes:
            if import_stmt not in para_adicionar:
                para_adicionar.append(import_stmt)

    if not para_adicionar:
        return code

    # Injeta após o bloco de imports existente
    primeiro_nao_import = next(
        (
            i for i, l in enumerate(linhas)
            if l.strip()
            and not l.startswith("import")
            and not l.startswith("from")
            and not l.startswith("#")
        ),
        0
    )

    linhas = (
        linhas[:primeiro_nao_import]
        + para_adicionar
        + [""]
        + linhas[primeiro_nao_import:]
    )
    return "\n".join(linhas)


def write_tests(state: dict) -> dict:
    """
    Agente Escritor — gera ou complementa os testes pytest.

    Recebe do state:
        - files: dict[str, str] — código fonte original
        - analysis: dict[str, list] — mapa gerado pelo Analisador
        - iteration: int — número da iteração atual
        - coverage_pct: float — cobertura da iteração anterior (0.0 na primeira)
        - uncovered_lines: dict[str, list[int]] — linhas não cobertas (vazio na primeira)

    Adiciona ao state:
        - generated_tests: str — código Python dos testes gerados
    """
    llm = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o"),
        temperature=0.2
    )

    prompt = render(
        "writer.j2",
        files=state["files"],
        analysis=state["analysis"],
        iteration=state["iteration"],
        coverage_pct=state.get("coverage_pct", 0.0),
        uncovered_lines=state.get("uncovered_lines", {})
    )

    response = llm.invoke([HumanMessage(content=prompt)])

    # Remove markdown code fences independente do formato
    generated_tests = response.content.strip()
    generated_tests = re.sub(r'^```[\w]*\n', '', generated_tests)
    generated_tests = re.sub(r'\n```$', '', generated_tests)
    generated_tests = generated_tests.strip()

    # Injeta imports faltantes que o LLM esqueceu de incluir
    generated_tests = _corrigir_imports(generated_tests)

    return {**state, "generated_tests": generated_tests}