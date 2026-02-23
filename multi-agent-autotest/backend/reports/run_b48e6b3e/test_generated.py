import pytest
from unittest.mock import patch, MagicMock
from analyzer import analyze_code
from reviewer import review_coverage
from writer import write_tests

# Tests for analyze_code function
@pytest.fixture
def mock_chat_openai():
    with patch('analyzer.ChatOpenAI') as MockChatOpenAI:
        yield MockChatOpenAI

@pytest.fixture
def mock_render():
    with patch('analyzer.render') as mock_render:
        yield mock_render

def test_analyze_code_happy_path(mock_chat_openai, mock_render):
    mock_llm = MagicMock()
    mock_chat_openai.return_value = mock_llm
    mock_llm.invoke.return_value.content = '{"functions": ["func1", "func2"]}'
    mock_render.return_value = "rendered prompt"

    state = {"files": {"file1.py": "def func1(): pass\ndef func2(): pass"}}
    result = analyze_code(state)

    assert result["analysis"]["file1.py"] == ["func1", "func2"]

def test_analyze_code_empty_file(mock_chat_openai, mock_render):
    mock_llm = MagicMock()
    mock_chat_openai.return_value = mock_llm
    mock_llm.invoke.return_value.content = '{"functions": []}'
    mock_render.return_value = "rendered prompt"

    state = {"files": {"file1.py": ""}}
    result = analyze_code(state)

    assert result["analysis"]["file1.py"] == []

def test_analyze_code_invalid_json_response(mock_chat_openai, mock_render):
    mock_llm = MagicMock()
    mock_chat_openai.return_value = mock_llm
    mock_llm.invoke.return_value.content = "invalid json"
    mock_render.return_value = "rendered prompt"

    state = {"files": {"file1.py": "def func1(): pass"}}
    result = analyze_code(state)

    assert result["analysis"]["file1.py"] == []

def test_analyze_code_missing_files_key():
    state = {}
    with pytest.raises(KeyError):
        analyze_code(state)

# Tests for review_coverage function
@pytest.fixture
def mock_chat_openai_reviewer():
    with patch('reviewer.ChatOpenAI') as MockChatOpenAI:
        yield MockChatOpenAI

@pytest.fixture
def mock_render_reviewer():
    with patch('reviewer.render') as mock_render:
        yield mock_render

def test_review_coverage_happy_path(mock_chat_openai_reviewer, mock_render_reviewer):
    mock_llm = MagicMock()
    mock_chat_openai_reviewer.return_value = mock_llm
    mock_llm.invoke.return_value.content = '{"should_iterate": true, "reason": "Coverage below threshold"}'
    mock_render_reviewer.return_value = "rendered prompt"

    state = {
        "coverage_pct": 75.0,
        "uncovered_lines": {"file1.py": [1, 2]},
        "iteration": 1,
        "threshold": 80.0,
        "max_iterations": 5
    }
    result = review_coverage(state)

    assert result["should_iterate"] is True
    assert result["review_reason"] == "Coverage below threshold"

def test_review_coverage_invalid_json_response(mock_chat_openai_reviewer, mock_render_reviewer):
    mock_llm = MagicMock()
    mock_chat_openai_reviewer.return_value = mock_llm
    mock_llm.invoke.return_value.content = "invalid json"
    mock_render_reviewer.return_value = "rendered prompt"

    state = {
        "coverage_pct": 75.0,
        "uncovered_lines": {"file1.py": [1, 2]},
        "iteration": 1,
        "threshold": 80.0,
        "max_iterations": 5
    }
    result = review_coverage(state)

    assert result["should_iterate"] is False
    assert result["review_reason"] == "Falha ao interpretar resposta do revisor — encerrando por segurança."

def test_review_coverage_missing_fields():
    state = {}
    with pytest.raises(KeyError):
        review_coverage(state)

# Tests for write_tests function
@pytest.fixture
def mock_chat_openai_writer():
    with patch('writer.ChatOpenAI') as MockChatOpenAI:
        yield MockChatOpenAI

@pytest.fixture
def mock_render_writer():
    with patch('writer.render') as mock_render:
        yield mock_render

def test_write_tests_happy_path(mock_chat_openai_writer, mock_render_writer):
    mock_llm = MagicMock()
    mock_chat_openai_writer.return_value = mock_llm
    mock_llm.invoke.return_value.content = "def test_func(): pass"
    mock_render_writer.return_value = "rendered prompt"

    state = {
        "files": {"file1.py": "def func1(): pass"},
        "analysis": {"file1.py": ["func1"]},
        "iteration": 1,
        "coverage_pct": 75.0,
        "uncovered_lines": {"file1.py": [1]}
    }
    result = write_tests(state)

    assert result["generated_tests"] == "def test_func(): pass"

def test_write_tests_empty_state(mock_chat_openai_writer, mock_render_writer):
    mock_llm = MagicMock()
    mock_chat_openai_writer.return_value = mock_llm
    mock_llm.invoke.return_value.content = ""
    mock_render_writer.return_value = "rendered prompt"

    state = {}
    result = write_tests(state)

    assert result["generated_tests"] == ""

def test_write_tests_missing_files_key():
    state = {"analysis": {"file1.py": ["func1"]}}
    with pytest.raises(KeyError):
        write_tests(state)

def test_write_tests_coverage_zero(mock_chat_openai_writer, mock_render_writer):
    mock_llm = MagicMock()
    mock_chat_openai_writer.return_value = mock_llm
    mock_llm.invoke.return_value.content = "def test_func(): pass"
    mock_render_writer.return_value = "rendered prompt"

    state = {
        "files": {"file1.py": "def func1(): pass"},
        "analysis": {"file1.py": ["func1"]},
        "iteration": 1,
        "coverage_pct": 0.0,
        "uncovered_lines": {"file1.py": [1]}
    }
    result = write_tests(state)

    assert result["generated_tests"] == "def test_func(): pass"