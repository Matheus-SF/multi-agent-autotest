from unittest import mock
import pytest
from analyzer import analyze_code
from reviewer import review_coverage
from writer import write_tests

# Testes para analyze_code

def test_analyze_code_missing_files_key():
    state = {}
    with pytest.raises(KeyError):
        analyze_code(state)

def test_analyze_code_empty_file_content():
    state = {"files": {"empty.py": ""}}
    with mock.patch('analyzer.render', return_value="prompt"), \
         mock.patch('analyzer.ChatOpenAI.invoke', return_value=mock.Mock(content='{"functions": []}')):
        result = analyze_code(state)
    assert result["analysis"]["empty.py"] == []

def test_analyze_code_invalid_llm_response():
    state = {"files": {"invalid.py": "def foo(): pass"}}
    with mock.patch('analyzer.render', return_value="prompt"), \
         mock.patch('analyzer.ChatOpenAI.invoke', return_value=mock.Mock(content='invalid json')):
        result = analyze_code(state)
    assert result["analysis"]["invalid.py"] == []

# Testes para review_coverage

def test_review_coverage_missing_fields():
    state = {}
    with pytest.raises(KeyError):
        review_coverage(state)

def test_review_coverage_unexpected_values():
    state = {
        "coverage_pct": -1.0,
        "uncovered_lines": {},
        "iteration": 1,
        "threshold": 100.0,
        "max_iterations": 10
    }
    with mock.patch('reviewer.render', return_value="prompt"), \
         mock.patch('reviewer.ChatOpenAI.invoke', return_value=mock.Mock(content='{"should_iterate": false, "reason": "Invalid values"}')):
        result = review_coverage(state)
    assert result["should_iterate"] is False
    assert result["review_reason"] == "Invalid values"

def test_review_coverage_unparsable_llm_response():
    state = {
        "coverage_pct": 50.0,
        "uncovered_lines": {"file.py": [1, 2]},
        "iteration": 1,
        "threshold": 80.0,
        "max_iterations": 10
    }
    with mock.patch('reviewer.render', return_value="prompt"), \
         mock.patch('reviewer.ChatOpenAI.invoke', return_value=mock.Mock(content='invalid json')):
        result = review_coverage(state)
    assert result["should_iterate"] is False
    assert result["review_reason"] == "Falha ao interpretar resposta do revisor — encerrando por segurança."

# Testes para write_tests

def test_write_tests_empty_state():
    state = {}
    with pytest.raises(KeyError):
        write_tests(state)

def test_write_tests_missing_files_key():
    state = {"analysis": {}, "iteration": 1, "coverage_pct": 0.0, "uncovered_lines": {}}
    with pytest.raises(KeyError):
        write_tests(state)

def test_write_tests_missing_analysis_key():
    state = {"files": {}, "iteration": 1, "coverage_pct": 0.0, "uncovered_lines": {}}
    with pytest.raises(KeyError):
        write_tests(state)

def test_write_tests_zero_coverage():
    state = {
        "files": {"file.py": "def foo(): pass"},
        "analysis": {"file.py": []},
        "iteration": 1,
        "coverage_pct": 0.0,
        "uncovered_lines": {"file.py": [1]}
    }
    with mock.patch('writer.render', return_value="prompt"), \
         mock.patch('writer.ChatOpenAI.invoke', return_value=mock.Mock(content='```python\ndef test_foo(): pass\n```')):
        result = write_tests(state)
    assert "generated_tests" in result
    assert "def test_foo():" in result["generated_tests"]

def test_write_tests_empty_uncovered_lines():
    state = {
        "files": {"file.py": "def foo(): pass"},
        "analysis": {"file.py": []},
        "iteration": 1,
        "coverage_pct": 50.0,
        "uncovered_lines": {}
    }
    with mock.patch('writer.render', return_value="prompt"), \
         mock.patch('writer.ChatOpenAI.invoke', return_value=mock.Mock(content='```python\ndef test_foo(): pass\n```')):
        result = write_tests(state)
    assert "generated_tests" in result
    assert "def test_foo():" in result["generated_tests"]