from langgraph.graph import StateGraph, END
from typing import TypedDict
from agents.analyzer import analyze_code
from agents.writer import write_tests
from agents.reviewer import review_coverage
from tools.executor import run_tests
import tempfile
import shutil
import uuid
from pathlib import Path


class AgentState(TypedDict):
    files: dict[str, str]
    threshold: float
    max_iterations: int
    analysis: dict[str, list]
    iteration: int
    should_iterate: bool
    review_reason: str
    generated_tests: str
    coverage_pct: float
    uncovered_lines: dict[str, list[int]]
    tests_passed: int
    tests_failed: int
    report_url: str
    report: dict


# Pasta fixa onde os reports HTML ficam salvos
REPORTS_DIR = Path(__file__).parent.parent / "reports"
REPORTS_DIR.mkdir(exist_ok=True)


def execute_tests(state: AgentState) -> AgentState:
    code_dir = tempfile.mkdtemp()

    # Diretório nomeado com UUID para não sobrescrever runs anteriores
    run_id = uuid.uuid4().hex[:8]
    tests_dir = REPORTS_DIR / f"run_{run_id}"
    tests_dir.mkdir(exist_ok=True)

    try:
        # Salva o código do usuário
        for filename, content in state["files"].items():
            filepath = Path(code_dir) / filename
            filepath.parent.mkdir(parents=True, exist_ok=True)
            filepath.write_text(content)

        # Salva os testes gerados
        tests_file = tests_dir / "test_generated.py"
        tests_file.write_text(state["generated_tests"])

        result = run_tests(code_dir, str(tests_dir))

        report = {
            "coverage_pct": result.coverage_pct,
            "uncovered_lines": result.uncovered_lines,
            "iteration": state["iteration"] + 1,
            "review_reason": state.get("review_reason", ""),
            "tests_code": state["generated_tests"],
            "success": result.success,
            "error": result.error_output,
            "tests_passed": result.tests_passed,
            "tests_failed": result.tests_failed,
            "report_url": f"/reports/run_{run_id}/htmlcov/index.html",
            "failed_tests": result.failed_tests or []
        }

        return {
            **state,
            "coverage_pct": result.coverage_pct,
            "uncovered_lines": result.uncovered_lines,
            "iteration": state["iteration"] + 1,
            "tests_passed": result.tests_passed,
            "tests_failed": result.tests_failed,
            "report_url": f"/reports/run_{run_id}/htmlcov/index.html",
            "report": report
        }
    finally:
        shutil.rmtree(code_dir, ignore_errors=True)


def should_continue(state: AgentState) -> str:
    if state["should_iterate"]:
        return "writer"
    return END


def build_graph() -> StateGraph:
    graph = StateGraph(AgentState)

    graph.add_node("analyzer", analyze_code)
    graph.add_node("writer", write_tests)
    graph.add_node("executor", execute_tests)
    graph.add_node("reviewer", review_coverage)

    graph.set_entry_point("analyzer")
    graph.add_edge("analyzer", "writer")
    graph.add_edge("writer", "executor")
    graph.add_edge("executor", "reviewer")

    graph.add_conditional_edges(
        "reviewer",
        should_continue,
        {"writer": "writer", END: END}
    )

    return graph.compile()


agent_graph = build_graph()