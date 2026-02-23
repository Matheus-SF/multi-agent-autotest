# test_analyzer.py
import pytest
from unittest.mock import patch, MagicMock
from analyzer import analyze_code

def test_analyze_code_happy_path():
    state = {"files": {"test.py": "def foo(): pass"}}
    mock_llm_response = MagicMock()
    mock_llm_response.content = '{"functions": ["foo"]}'
    with patch("analyzer.ChatOpenAI.invoke", return_value=mock_llm_response):
        result = analyze_code(state)
    assert result["analysis"] == {"test.py": ["foo"]}

def test_analyze_code_missing_files_key():
    state = {}
    with pytest.raises(KeyError):
        analyze_code(state)

def test_analyze_code_empty_file_content():
    state = {"files": {"empty.py": ""}}
    mock_llm_response = MagicMock()
    mock_llm_response.content = '{"functions": []}'
    with patch("analyzer.ChatOpenAI.invoke", return_value=mock_llm_response):
        result = analyze_code(state)
    assert result["analysis"] == {"empty.py": []}

def test_analyze_code_invalid_llm_response():
    state = {"files": {"test.py": "def foo(): pass"}}
    mock_llm_response = MagicMock()
    mock_llm_response.content = "invalid json"
    with patch("analyzer.ChatOpenAI.invoke", return_value=mock_llm_response):
        result = analyze_code(state)
    assert result["analysis"] == {"test.py": []}

# test_executor.py
import pytest
from unittest.mock import patch, MagicMock
from executor import run_tests, _parse_coverage, _parse_junit, CoverageResult
from pathlib import Path

def test_run_tests_nonexistent_code_dir():
    with patch("executor.subprocess.run") as mock_run:
        mock_run.side_effect = FileNotFoundError
        result = run_tests("nonexistent_code_dir", "tests_dir")
    assert not result.success
    assert result.error_output == "FileNotFoundError"

def test_run_tests_nonexistent_tests_dir():
    with patch("executor.subprocess.run") as mock_run:
        mock_run.side_effect = FileNotFoundError
        result = run_tests("code_dir", "nonexistent_tests_dir")
    assert not result.success
    assert result.error_output == "FileNotFoundError"

def test_run_tests_timeout():
    with patch("executor.subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="pytest", timeout=120)
        result = run_tests("code_dir", "tests_dir")
    assert not result.success
    assert result.error_output == "Timeout: execução excedeu 2 minutos"

def test_parse_coverage_nonexistent_file():
    with patch("executor.ET.parse") as mock_parse:
        mock_parse.side_effect = FileNotFoundError
        with pytest.raises(FileNotFoundError):
            _parse_coverage(Path("nonexistent_coverage.xml"))

def test_parse_coverage_malformed_file():
    with patch("executor.ET.parse") as mock_parse:
        mock_parse.side_effect = ET.ParseError
        with pytest.raises(ET.ParseError):
            _parse_coverage(Path("malformed_coverage.xml"))

def test_parse_junit_nonexistent_file():
    with patch("executor.ET.parse") as mock_parse:
        mock_parse.side_effect = FileNotFoundError
        passed, failed, failed_tests = _parse_junit(Path("nonexistent_junit.xml"))
    assert passed == 0
    assert failed == 0
    assert failed_tests == []

def test_parse_junit_malformed_file():
    with patch("executor.ET.parse") as mock_parse:
        mock_parse.side_effect = ET.ParseError
        passed, failed, failed_tests = _parse_junit(Path("malformed_junit.xml"))
    assert passed == 0
    assert failed == 0
    assert failed_tests == []

# test_reviewer.py
import pytest
from unittest.mock import patch, MagicMock
from reviewer import review_coverage

def test_review_coverage_missing_fields():
    state = {}
    with pytest.raises(KeyError):
        review_coverage(state)

def test_review_coverage_invalid_values():
    state = {
        "coverage_pct": "invalid",
        "uncovered_lines": "invalid",
        "iteration": "invalid",
        "threshold": "invalid",
        "max_iterations": "invalid"
    }
    with pytest.raises(TypeError):
        review_coverage(state)

def test_review_coverage_invalid_llm_response():
    state = {
        "coverage_pct": 50.0,
        "uncovered_lines": {},
        "iteration": 1,
        "threshold": 75.0,
        "max_iterations": 5
    }
    mock_llm_response = MagicMock()
    mock_llm_response.content = "invalid json"
    with patch("reviewer.ChatOpenAI.invoke", return_value=mock_llm_response):
        result = review_coverage(state)
    assert not result["should_iterate"]
    assert result["review_reason"] == "Falha ao interpretar resposta do revisor — encerrando por segurança."

# test_writer.py
import pytest
from unittest.mock import patch, MagicMock
from writer import write_tests

def test_write_tests_empty_state():
    state = {}
    with pytest.raises(KeyError):
        write_tests(state)

def test_write_tests_missing_files_key():
    state = {"analysis": {}, "iteration": 0, "coverage_pct": 0.0, "uncovered_lines": {}}
    with pytest.raises(KeyError):
        write_tests(state)

def test_write_tests_missing_analysis_key():
    state = {"files": {}, "iteration": 0, "coverage_pct": 0.0, "uncovered_lines": {}}
    with pytest.raises(KeyError):
        write_tests(state)

def test_write_tests_missing_iteration_key():
    state = {"files": {}, "analysis": {}, "coverage_pct": 0.0, "uncovered_lines": {}}
    with pytest.raises(KeyError):
        write_tests(state)

def test_write_tests_missing_coverage_pct_key():
    state = {"files": {}, "analysis": {}, "iteration": 0, "uncovered_lines": {}}
    with pytest.raises(KeyError):
        write_tests(state)

def test_write_tests_missing_uncovered_lines_key():
    state = {"files": {}, "analysis": {}, "iteration": 0, "coverage_pct": 0.0}
    with pytest.raises(KeyError):
        write_tests(state)

def test_write_tests_negative_coverage_pct():
    state = {"files": {}, "analysis": {}, "iteration": 0, "coverage_pct": -10.0, "uncovered_lines": {}}
    with pytest.raises(ValueError):
        write_tests(state)

def test_write_tests_negative_iteration():
    state = {"files": {}, "analysis": {}, "iteration": -1, "coverage_pct": 0.0, "uncovered_lines": {}}
    with pytest.raises(ValueError):
        write_tests(state)