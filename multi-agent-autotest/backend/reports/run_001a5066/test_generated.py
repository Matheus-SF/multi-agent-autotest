import pytest
from unittest.mock import patch, MagicMock
from analyzer import analyze_code
from reviewer import review_coverage
from writer import write_tests

# Testes para analyze_code
def test_analyze_code_happy_path():
    state = {"files": {"test.py": "def foo(): pass"}}
    with patch("analyzer.ChatOpenAI") as MockChatOpenAI, \
         patch("analyzer.render") as mock_render:
        mock_llm = MockChatOpenAI.return_value
        mock_llm.invoke.return_value.content = '{"functions": ["foo"]}'
        mock_render.return_value = "rendered prompt"
        result = analyze_code(state)
        assert result["analysis"]["test.py"] == ["foo"]

def test_analyze_code_no_files_key():
    state = {}
    with pytest.raises(KeyError):
        analyze_code(state)

def test_analyze_code_empty_file_content():
    state = {"files": {"empty.py": ""}}
    with patch("analyzer.ChatOpenAI") as MockChatOpenAI, \
         patch("analyzer.render") as mock_render:
        mock_llm = MockChatOpenAI.return_value
        mock_llm.invoke.return_value.content = '{"functions": []}'
        mock_render.return_value = "rendered prompt"
        result = analyze_code(state)
        assert result["analysis"]["empty.py"] == []

def test_analyze_code_invalid_json_response():
    state = {"files": {"test.py": "def foo(): pass"}}
    with patch("analyzer.ChatOpenAI") as MockChatOpenAI, \
         patch("analyzer.render") as mock_render:
        mock_llm = MockChatOpenAI.return_value
        mock_llm.invoke.return_value.content = "invalid json"
        mock_render.return_value = "rendered prompt"
        result = analyze_code(state)
        assert result["analysis"]["test.py"] == []

# Testes para review_coverage
def test_review_coverage_happy_path():
    state = {
        "coverage_pct": 75.0,
        "uncovered_lines": {"test.py": [1, 2]},
        "iteration": 1,
        "threshold": 80.0,
        "max_iterations": 5
    }
    with patch("reviewer.ChatOpenAI") as MockChatOpenAI, \
         patch("reviewer.render") as mock_render:
        mock_llm = MockChatOpenAI.return_value
        mock_llm.invoke.return_value.content = '{"should_iterate": true, "reason": "Continue"}'
        mock_render.return_value = "rendered prompt"
        result = review_coverage(state)
        assert result["should_iterate"] is True
        assert result["review_reason"] == "Continue"

def test_review_coverage_missing_fields():
    state = {}
    with pytest.raises(KeyError):
        review_coverage(state)

def test_review_coverage_invalid_json_response():
    state = {
        "coverage_pct": 75.0,
        "uncovered_lines": {"test.py": [1, 2]},
        "iteration": 1,
        "threshold": 80.0,
        "max_iterations": 5
    }
    with patch("reviewer.ChatOpenAI") as MockChatOpenAI, \
         patch("reviewer.render") as mock_render:
        mock_llm = MockChatOpenAI.return_value
        mock_llm.invoke.return_value.content = "invalid json"
        mock_render.return_value = "rendered prompt"
        result = review_coverage(state)
        assert result["should_iterate"] is False
        assert result["review_reason"] == "Falha ao interpretar resposta do revisor — encerrando por segurança."

# Testes para write_tests
def test_write_tests_happy_path():
    state = {
        "files": {"test.py": "def foo(): pass"},
        "analysis": {"test.py": ["foo"]},
        "iteration": 1,
        "coverage_pct": 50.0,
        "uncovered_lines": {"test.py": [1]}
    }
    with patch("writer.ChatOpenAI") as MockChatOpenAI, \
         patch("writer.render") as mock_render:
        mock_llm = MockChatOpenAI.return_value
        mock_llm.invoke.return_value.content = "def test_foo(): pass"
        mock_render.return_value = "rendered prompt"
        result = write_tests(state)
        assert result["generated_tests"] == "def test_foo(): pass"

def test_write_tests_empty_state():
    state = {}
    with pytest.raises(KeyError):
        write_tests(state)

def test_write_tests_no_files_key():
    state = {"analysis": {"test.py": ["foo"]}}
    with pytest.raises(KeyError):
        write_tests(state)

def test_write_tests_no_analysis_key():
    state = {"files": {"test.py": "def foo(): pass"}}
    with pytest.raises(KeyError):
        write_tests(state)

def test_write_tests_coverage_zero():
    state = {
        "files": {"test.py": "def foo(): pass"},
        "analysis": {"test.py": ["foo"]},
        "iteration": 1,
        "coverage_pct": 0.0,
        "uncovered_lines": {"test.py": [1]}
    }
    with patch("writer.ChatOpenAI") as MockChatOpenAI, \
         patch("writer.render") as mock_render:
        mock_llm = MockChatOpenAI.return_value
        mock_llm.invoke.return_value.content = "def test_foo(): pass"
        mock_render.return_value = "rendered prompt"
        result = write_tests(state)
        assert result["generated_tests"] == "def test_foo(): pass"

def test_write_tests_empty_uncovered_lines():
    state = {
        "files": {"test.py": "def foo(): pass"},
        "analysis": {"test.py": ["foo"]},
        "iteration": 1,
        "coverage_pct": 50.0,
        "uncovered_lines": {}
    }
    with patch("writer.ChatOpenAI") as MockChatOpenAI, \
         patch("writer.render") as mock_render:
        mock_llm = MockChatOpenAI.return_value
        mock_llm.invoke.return_value.content = "def test_foo(): pass"
        mock_render.return_value = "rendered prompt"
        result = write_tests(state)
        assert result["generated_tests"] == "def test_foo(): pass"