# test_analyzer.py
import pytest
from unittest.mock import patch, MagicMock
from analyzer import analyze_code

def test_analyze_code_happy_path():
    state = {"files": {"test.py": "def foo(): pass"}}
    mock_llm = MagicMock()
    mock_llm.invoke.return_value.content = '{"functions": ["foo"]}'
    with patch('analyzer.ChatOpenAI', return_value=mock_llm):
        result = analyze_code(state)
    assert result["analysis"]["test.py"] == ["foo"]

def test_analyze_code_no_files_key():
    state = {}
    with pytest.raises(KeyError):
        analyze_code(state)

def test_analyze_code_empty_file_content():
    state = {"files": {"empty.py": ""}}
    mock_llm = MagicMock()
    mock_llm.invoke.return_value.content = '{"functions": []}'
    with patch('analyzer.ChatOpenAI', return_value=mock_llm):
        result = analyze_code(state)
    assert result["analysis"]["empty.py"] == []

def test_analyze_code_invalid_json_response():
    state = {"files": {"test.py": "def foo(): pass"}}
    mock_llm = MagicMock()
    mock_llm.invoke.return_value.content = 'invalid json'
    with patch('analyzer.ChatOpenAI', return_value=mock_llm):
        result = analyze_code(state)
    assert result["analysis"]["test.py"] == []

# test_executor.py
import pytest
from unittest.mock import patch, MagicMock
from executor import run_tests, _parse_coverage, _parse_junit, CoverageResult
from pathlib import Path

def test_run_tests_code_dir_not_exist():
    with patch('executor.subprocess.run') as mock_run:
        mock_run.side_effect = FileNotFoundError
        result = run_tests("nonexistent_code_dir", "tests_dir")
    assert not result.success
    assert result.error_output == "FileNotFoundError"

def test_run_tests_tests_dir_not_exist():
    with patch('executor.subprocess.run') as mock_run:
        mock_run.side_effect = FileNotFoundError
        result = run_tests("code_dir", "nonexistent_tests_dir")
    assert not result.success
    assert result.error_output == "FileNotFoundError"

def test_run_tests_timeout():
    with patch('executor.subprocess.run') as mock_run:
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="pytest", timeout=120)
        result = run_tests("code_dir", "tests_dir")
    assert not result.success
    assert result.error_output == "Timeout: execução excedeu 2 minutos"

def test_parse_coverage_file_not_exist():
    with pytest.raises(FileNotFoundError):
        _parse_coverage(Path("nonexistent_coverage.xml"))

def test_parse_coverage_malformed_xml():
    with patch('executor.ET.parse', side_effect=ET.ParseError):
        with pytest.raises(ET.ParseError):
            _parse_coverage(Path("malformed_coverage.xml"))

def test_parse_junit_file_not_exist():
    with pytest.raises(FileNotFoundError):
        _parse_junit(Path("nonexistent_junit.xml"))

def test_parse_junit_malformed_xml():
    with patch('executor.ET.parse', side_effect=ET.ParseError):
        passed, failed, failed_tests = _parse_junit(Path("malformed_junit.xml"))
    assert passed == 0
    assert failed == 0
    assert failed_tests == []

# test_reviewer.py
import pytest
from unittest.mock import patch, MagicMock
from reviewer import review_coverage

def test_review_coverage_happy_path():
    state = {
        "coverage_pct": 80.0,
        "uncovered_lines": {},
        "iteration": 1,
        "threshold": 90.0,
        "max_iterations": 5
    }
    mock_llm = MagicMock()
    mock_llm.invoke.return_value.content = '{"should_iterate": true, "reason": "Coverage below threshold."}'
    with patch('reviewer.ChatOpenAI', return_value=mock_llm):
        result = review_coverage(state)
    assert result["should_iterate"]
    assert result["review_reason"] == "Coverage below threshold."

def test_review_coverage_missing_fields():
    state = {}
    with pytest.raises(KeyError):
        review_coverage(state)

def test_review_coverage_invalid_json_response():
    state = {
        "coverage_pct": 80.0,
        "uncovered_lines": {},
        "iteration": 1,
        "threshold": 90.0,
        "max_iterations": 5
    }
    mock_llm = MagicMock()
    mock_llm.invoke.return_value.content = 'invalid json'
    with patch('reviewer.ChatOpenAI', return_value=mock_llm):
        result = review_coverage(state)
    assert not result["should_iterate"]
    assert result["review_reason"] == "Falha ao interpretar resposta do revisor — encerrando por segurança."

# test_writer.py
import pytest
from unittest.mock import patch, MagicMock
from writer import write_tests

def test_write_tests_happy_path():
    state = {
        "files": {"test.py": "def foo(): pass"},
        "analysis": {"test.py": ["foo"]},
        "iteration": 1,
        "coverage_pct": 50.0,
        "uncovered_lines": {"test.py": [1]}
    }
    mock_llm = MagicMock()
    mock_llm.invoke.return_value.content = 'def test_foo(): assert foo() is None'
    with patch('writer.ChatOpenAI', return_value=mock_llm):
        result = write_tests(state)
    assert "generated_tests" in result
    assert "def test_foo()" in result["generated_tests"]

def test_write_tests_empty_state():
    state = {}
    with pytest.raises(KeyError):
        write_tests(state)

def test_write_tests_missing_files():
    state = {
        "analysis": {"test.py": ["foo"]},
        "iteration": 1,
        "coverage_pct": 50.0,
        "uncovered_lines": {"test.py": [1]}
    }
    with pytest.raises(KeyError):
        write_tests(state)

def test_write_tests_negative_coverage_pct():
    state = {
        "files": {"test.py": "def foo(): pass"},
        "analysis": {"test.py": ["foo"]},
        "iteration": 1,
        "coverage_pct": -10.0,
        "uncovered_lines": {"test.py": [1]}
    }
    with pytest.raises(ValueError):
        write_tests(state)

def test_write_tests_negative_iteration():
    state = {
        "files": {"test.py": "def foo(): pass"},
        "analysis": {"test.py": ["foo"]},
        "iteration": -1,
        "coverage_pct": 50.0,
        "uncovered_lines": {"test.py": [1]}
    }
    with pytest.raises(ValueError):
        write_tests(state)