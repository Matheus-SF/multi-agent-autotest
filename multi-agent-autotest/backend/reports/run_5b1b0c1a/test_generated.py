from unittest.mock import patch, MagicMock
import pytest
from executor import run_tests, _parse_coverage, _parse_junit, CoverageResult
from pathlib import Path

import subprocess
import xml.etree.ElementTree as ET

@pytest.fixture
def mock_subprocess_run():
    with patch('executor.subprocess.run') as mock_run:
        yield mock_run

@pytest.fixture
def mock_path_exists():
    with patch('executor.Path.exists') as mock_exists:
        yield mock_exists

@pytest.fixture
def mock_et_parse():
    with patch('executor.ET.parse') as mock_parse:
        yield mock_parse

def test_run_tests_success(mock_subprocess_run, mock_path_exists):
    mock_subprocess_run.return_value = MagicMock(stdout="stdout", stderr="stderr")
    mock_path_exists.side_effect = lambda p: True

    result = run_tests("/fake/code_dir", "/fake/tests_dir")

    assert result.success
    assert result.coverage_pct > 0

def test_run_tests_code_dir_not_exists(mock_subprocess_run, mock_path_exists):
    mock_subprocess_run.return_value = MagicMock(stdout="stdout", stderr="stderr")
    mock_path_exists.side_effect = lambda p: False if "/fake/tests_dir/coverage.xml" in str(p) else True

    result = run_tests("/fake/code_dir", "/fake/tests_dir")

    assert not result.success
    assert result.coverage_pct == 0.0

def test_run_tests_timeout(mock_subprocess_run):
    mock_subprocess_run.side_effect = subprocess.TimeoutExpired(cmd="docker run", timeout=120)

    result = run_tests("/fake/code_dir", "/fake/tests_dir")

    assert not result.success
    assert result.error_output == "Timeout: execução excedeu 2 minutos"

def test_parse_coverage_success(mock_et_parse):
    mock_tree = MagicMock()
    mock_tree.getroot.return_value.attrib = {"line-rate": "0.75"}
    mock_et_parse.return_value = mock_tree

    result = _parse_coverage(Path("/fake/coverage.xml"))

    assert result.success
    assert result.coverage_pct == 75.0

def test_parse_coverage_file_not_found(mock_et_parse):
    mock_et_parse.side_effect = FileNotFoundError

    result = _parse_coverage(Path("/fake/coverage.xml"))

    assert not result.success
    assert result.coverage_pct == 0.0

def test_parse_junit_success(mock_et_parse):
    mock_tree = MagicMock()
    mock_tree.getroot.return_value.find.return_value.attrib = {"tests": "10", "failures": "2", "errors": "1"}
    mock_et_parse.return_value = mock_tree

    passed, failed, failed_tests = _parse_junit(Path("/fake/junit.xml"))

    assert passed == 7
    assert failed == 3

def test_parse_junit_file_not_found(mock_et_parse):
    mock_et_parse.side_effect = FileNotFoundError

    passed, failed, failed_tests = _parse_junit(Path("/fake/junit.xml"))

    assert passed == 0
    assert failed == 0

def test_parse_junit_malformed_xml(mock_et_parse):
    mock_et_parse.side_effect = ET.ParseError

    passed, failed, failed_tests = _parse_junit(Path("/fake/junit.xml"))

    assert passed == 0
    assert failed == 0