from unittest.mock import patch, MagicMock
import pytest
from pathlib import Path
from analyzer import analyze_code
from executor import run_tests, _parse_coverage, _parse_junit, CoverageResult
from reviewer import review_coverage
from writer import write_tests


# Tests for analyze_code
def test_analyze_code_happy_path():
    state = {"files": {"test.py": "def foo(): pass"}}
    with patch("analyzer.ChatOpenAI") as MockChatOpenAI, patch("analyzer.render") as mock_render:
        mock_llm = MockChatOpenAI.return_value
        mock_llm.invoke.return_value.content = '{"functions": ["foo"]}'
        mock_render.return_value = "prompt"
        result = analyze_code(state)
        assert result["analysis"] == {"test.py": ["foo"]}


def test_analyze_code_no_files_key():
    state = {}
    with pytest.raises(KeyError):
        analyze_code(state)


def test_analyze_code_empty_file_content():
    state = {"files": {"empty.py": ""}}
    with patch("analyzer.ChatOpenAI") as MockChatOpenAI, patch("analyzer.render") as mock_render:
        mock_llm = MockChatOpenAI.return_value
        mock_llm.invoke.return_value.content = '{"functions": []}'
        mock_render.return_value = "prompt"
        result = analyze_code(state)
        assert result["analysis"] == {"empty.py": []}


def test_analyze_code_invalid_json_response():
    state = {"files": {"test.py": "def foo(): pass"}}
    with patch("analyzer.ChatOpenAI") as MockChatOpenAI, patch("analyzer.render") as mock_render:
        mock_llm = MockChatOpenAI.return_value
        mock_llm.invoke.return_value.content = "invalid json"
        mock_render.return_value = "prompt"
        result = analyze_code(state)
        assert result["analysis"] == {"test.py": []}


# Tests for run_tests
def test_run_tests_happy_path():
    with patch("executor.subprocess.run") as mock_run, patch("executor._parse_coverage") as mock_parse_coverage, patch("executor._parse_junit") as mock_parse_junit:
        mock_run.return_value.stdout = "stdout"
        mock_run.return_value.stderr = "stderr"
        mock_parse_coverage.return_value = CoverageResult(True, 75.0, {})
        mock_parse_junit.return_value = (10, 0, [])
        result = run_tests("/code", "/tests")
        assert result.success
        assert result.coverage_pct == 75.0
        assert result.tests_passed == 10
        assert result.tests_failed == 0


def test_run_tests_code_dir_not_exist():
    with patch("executor.subprocess.run", side_effect=FileNotFoundError):
        result = run_tests("/invalid_code", "/tests")
        assert not result.success
        assert "No such file or directory" in result.error_output


def test_run_tests_tests_dir_not_exist():
    with patch("executor.subprocess.run", side_effect=FileNotFoundError):
        result = run_tests("/code", "/invalid_tests")
        assert not result.success
        assert "No such file or directory" in result.error_output


def test_run_tests_timeout():
    with patch("executor.subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="cmd", timeout=120)):
        result = run_tests("/code", "/tests")
        assert not result.success
        assert "Timeout" in result.error_output


# Tests for _parse_coverage
def test_parse_coverage_happy_path():
    with patch("executor.ET.parse") as mock_parse:
        mock_root = MagicMock()
        mock_root.attrib = {"line-rate": "0.75"}
        mock_parse.return_value.getroot.return_value = mock_root
        result = _parse_coverage(Path("coverage.xml"))
        assert result.coverage_pct == 75.0


def test_parse_coverage_file_not_exist():
    with pytest.raises(FileNotFoundError):
        _parse_coverage(Path("nonexistent.xml"))


def test_parse_coverage_malformed_xml():
    with patch("executor.ET.parse", side_effect=ET.ParseError):
        with pytest.raises(ET.ParseError):
            _parse_coverage(Path("malformed.xml"))


# Tests for _parse_junit
def test_parse_junit_happy_path():
    with patch("executor.ET.parse") as mock_parse:
        mock_root = MagicMock()
        mock_suite = MagicMock()
        mock_suite.attrib = {"tests": "10", "failures": "2", "errors": "1"}
        mock_root.find.return_value = mock_suite
        mock_parse.return_value.getroot.return_value = mock_root
        result = _parse_junit(Path("junit.xml"))
        assert result == (7, 3, [])


def test_parse_junit_file_not_exist():
    with pytest.raises(FileNotFoundError):
        _parse_junit(Path("nonexistent.xml"))


def test_parse_junit_malformed_xml():
    with patch("executor.ET.parse", side_effect=ET.ParseError):
        with pytest.raises(ET.ParseError):
            _parse_junit(Path("malformed.xml"))


# Tests for review_coverage
def test_review_coverage_happy_path():
    state = {
        "coverage_pct": 80.0,
        "uncovered_lines": {},
        "iteration": 1,
        "threshold": 85.0,
        "max_iterations": 5
    }
    with patch("reviewer.ChatOpenAI") as MockChatOpenAI, patch("reviewer.render") as mock_render:
        mock_llm = MockChatOpenAI.return_value
        mock_llm.invoke.return_value.content = '{"should_iterate": true, "reason": "Coverage below threshold"}'
        mock_render.return_value = "prompt"
        result = review_coverage(state)
        assert result["should_iterate"]
        assert result["review_reason"] == "Coverage below threshold"


def test_review_coverage_invalid_json_response():
    state = {
        "coverage_pct": 80.0,
        "uncovered_lines": {},
        "iteration": 1,
        "threshold": 85.0,
        "max_iterations": 5
    }
    with patch("reviewer.ChatOpenAI") as MockChatOpenAI, patch("reviewer.render") as mock_render:
        mock_llm = MockChatOpenAI.return_value
        mock_llm.invoke.return_value.content = "invalid json"
        mock_render.return_value = "prompt"
        result = review_coverage(state)
        assert not result["should_iterate"]
        assert "Falha ao interpretar resposta do revisor" in result["review_reason"]


# Tests for write_tests
def test_write_tests_happy_path():
    state = {
        "files": {"test.py": "def foo(): pass"},
        "analysis": {"test.py": ["foo"]},
        "iteration": 1,
        "coverage_pct": 75.0,
        "uncovered_lines": {}
    }
    with patch("writer.ChatOpenAI") as MockChatOpenAI, patch("writer.render") as mock_render:
        mock_llm = MockChatOpenAI.return_value
        mock_llm.invoke.return_value.content = "def test_foo(): pass"
        mock_render.return_value = "prompt"
        result = write_tests(state)
        assert "generated_tests" in result
        assert "def test_foo(): pass" in result["generated_tests"]


def test_write_tests_empty_state():
    state = {}
    with pytest.raises(KeyError):
        write_tests(state)


def test_write_tests_negative_coverage_pct():
    state = {
        "files": {"test.py": "def foo(): pass"},
        "analysis": {"test.py": ["foo"]},
        "iteration": 1,
        "coverage_pct": -10.0,
        "uncovered_lines": {}
    }
    with patch("writer.ChatOpenAI") as MockChatOpenAI, patch("writer.render") as mock_render:
        mock_llm = MockChatOpenAI.return_value
        mock_llm.invoke.return_value.content = "def test_foo(): pass"
        mock_render.return_value = "prompt"
        result = write_tests(state)
        assert "generated_tests" in result
        assert "def test_foo(): pass" in result["generated_tests"]


def test_write_tests_negative_iteration():
    state = {
        "files": {"test.py": "def foo(): pass"},
        "analysis": {"test.py": ["foo"]},
        "iteration": -1,
        "coverage_pct": 75.0,
        "uncovered_lines": {}
    }
    with patch("writer.ChatOpenAI") as MockChatOpenAI, patch("writer.render") as mock_render:
        mock_llm = MockChatOpenAI.return_value
        mock_llm.invoke.return_value.content = "def test_foo(): pass"
        mock_render.return_value = "prompt"
        result = write_tests(state)
        assert "generated_tests" in result
        assert "def test_foo(): pass" in result["generated_tests"]