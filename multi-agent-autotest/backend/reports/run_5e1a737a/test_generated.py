from unittest import mock
import pytest
from pathlib import Path
from executor import run_tests, _parse_coverage, _parse_junit, CoverageResult

@pytest.fixture
def mock_subprocess_run():
    with mock.patch('executor.subprocess.run') as mock_run:
        yield mock_run

@pytest.fixture
def mock_path_exists():
    with mock.patch('executor.Path.exists') as mock_exists:
        yield mock_exists

@pytest.fixture
def mock_et_parse():
    with mock.patch('executor.ET.parse') as mock_parse:
        yield mock_parse

def test_run_tests_happy_path(mock_subprocess_run, mock_path_exists, mock_et_parse):
    mock_subprocess_run.return_value.stdout = "stdout"
    mock_subprocess_run.return_value.stderr = "stderr"
    mock_path_exists.side_effect = lambda p: True
    mock_et_parse.return_value.getroot.return_value.attrib = {"line-rate": "0.8"}

    result = run_tests("/fake/code_dir", "/fake/tests_dir")

    assert result.success
    assert result.coverage_pct == 80.0

def test_run_tests_code_dir_not_exist(mock_subprocess_run, mock_path_exists):
    mock_path_exists.side_effect = lambda p: False

    result = run_tests("/fake/code_dir", "/fake/tests_dir")

    assert not result.success
    assert result.coverage_pct == 0.0
    assert "stderr" in result.error_output

def test_run_tests_timeout(mock_subprocess_run):
    mock_subprocess_run.side_effect = subprocess.TimeoutExpired(cmd="docker run", timeout=120)

    result = run_tests("/fake/code_dir", "/fake/tests_dir")

    assert not result.success
    assert result.coverage_pct == 0.0
    assert "Timeout" in result.error_output

def test_parse_coverage_happy_path(mock_et_parse):
    mock_et_parse.return_value.getroot.return_value.attrib = {"line-rate": "0.75"}
    mock_et_parse.return_value.getroot.return_value.iter.return_value = []

    result = _parse_coverage(Path("/fake/coverage.xml"))

    assert result.success
    assert result.coverage_pct == 75.0

def test_parse_coverage_file_not_exist():
    with pytest.raises(FileNotFoundError):
        _parse_coverage(Path("/non/existent/coverage.xml"))

def test_parse_coverage_malformed_xml(mock_et_parse):
    mock_et_parse.side_effect = ET.ParseError

    with pytest.raises(ET.ParseError):
        _parse_coverage(Path("/fake/coverage.xml"))

def test_parse_junit_happy_path(mock_et_parse):
    mock_et_parse.return_value.getroot.return_value.find.return_value.attrib = {
        "tests": "10", "failures": "2", "errors": "1"
    }
    mock_et_parse.return_value.getroot.return_value.iter.return_value = []

    passed, failed, failed_tests = _parse_junit(Path("/fake/junit.xml"))

    assert passed == 7
    assert failed == 3
    assert failed_tests == []

def test_parse_junit_file_not_exist():
    with pytest.raises(FileNotFoundError):
        _parse_junit(Path("/non/existent/junit.xml"))

def test_parse_junit_malformed_xml(mock_et_parse):
    mock_et_parse.side_effect = ET.ParseError

    passed, failed, failed_tests = _parse_junit(Path("/fake/junit.xml"))

    assert passed == 0
    assert failed == 0
    assert failed_tests == []