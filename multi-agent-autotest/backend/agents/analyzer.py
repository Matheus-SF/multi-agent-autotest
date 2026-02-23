from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from prompts.loader import render
import json
import os


def analyze_code(state: dict) -> dict:
    """
    Agente Analisador — lê os arquivos .py e produz um mapa estruturado.

    Recebe do state:
        - files: dict[str, str] — {nome_arquivo: conteúdo}

    Adiciona ao state:
        - analysis: dict[str, list] — {nome_arquivo: [funções analisadas]}
    """
    llm = ChatOpenAI(
    model=os.getenv("OPENAI_MODEL", "gpt-4o"),
    temperature=0
    )
    files: dict[str, str] = state["files"]
    analysis = {}

    for filename, content in files.items():
        # Renderiza o prompt com as variáveis do arquivo atual
        prompt = render("analyzer.j2", filename=filename, content=content)

        response = llm.invoke([HumanMessage(content=prompt)])

        try:
            parsed = json.loads(response.content)
            analysis[filename] = parsed["functions"]
        except json.JSONDecodeError:
            analysis[filename] = []
            print(f"[Analyzer] Failed to parse response for {filename}")

    return {**state, "analysis": analysis}