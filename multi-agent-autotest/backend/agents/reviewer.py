from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from prompts.loader import render
import json
import os


def review_coverage(state: dict) -> dict:
    """
    Agente Revisor — analisa o resultado do coverage e decide se itera ou encerra.

    Recebe do state:
        - coverage_pct: float — cobertura atual
        - uncovered_lines: dict[str, list[int]] — linhas não cobertas
        - iteration: int — iteração atual
        - threshold: float — meta de cobertura configurada pelo usuário
        - max_iterations: int — limite de iterações

    Adiciona ao state:
        - should_iterate: bool — decisão do revisor
        - review_reason: str — justificativa da decisão
    """
    llm = ChatOpenAI(
    model=os.getenv("OPENAI_MODEL", "gpt-4o"),
    temperature=0  # decisão binária
    )
    prompt = render(
        "reviewer.j2",
        coverage_pct=state["coverage_pct"],
        uncovered_lines=state["uncovered_lines"],
        iteration=state["iteration"],
        threshold=state["threshold"],
        max_iterations=state["max_iterations"]
    )

    response = llm.invoke([HumanMessage(content=prompt)])

    try:
        parsed = json.loads(response.content)
        should_iterate = parsed["should_iterate"]
        reason = parsed["reason"]
    except json.JSONDecodeError:
        # Em caso de falha no parse, encerramos por segurança
        # para não entrar em loop infinito
        should_iterate = False
        reason = "Falha ao interpretar resposta do revisor — encerrando por segurança."
        print("[Reviewer] Failed to parse response")

    return {**state, "should_iterate": should_iterate, "review_reason": reason}