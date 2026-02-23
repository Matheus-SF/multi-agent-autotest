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

def test_run_tests_coverage_file_not_exists(mock_subprocess_run, mock_path_exists):
    mock_subprocess_run.return_value.stdout = "stdout"
    mock_subprocess_run.return_value.stderr = "stderr"
    mock_path_exists.side_effect = lambda x: False if 'coverage.xml' in str(x) else True

    result = run_tests("code_dir", "tests_dir")

    assert result.success is False
    assert result.coverage_pct == 0.0
    assert result.uncovered_lines == {}
    assert result.error_output == "stderr"

def test_run_tests_junit_file_not_exists(mock_subprocess_run, mock_path_exists, mock_et_parse):
    mock_subprocess_run.return_value.stdout = "stdout"
    mock_subprocess_run.return_value.stderr = "stderr"
    mock_path_exists.side_effect = lambda x: True if 'coverage.xml' in str(x) else False
    mock_et_parse.return_value.getroot.return_value.attrib = {"line-rate": "0.8"}

    result = run_tests("code_dir", "tests_dir")

    assert result.success is True
    assert result.coverage_pct == 80.0
    assert result.uncovered_lines == {}
    assert result.tests_passed == 0
    assert result.tests_failed == 0
    assert result.failed_tests == []

def test_run_tests_timeout(mock_subprocess_run):
    mock_subprocess_run.side_effect = subprocess.TimeoutExpired(cmd="cmd", timeout=120)

    result = run_tests("code_dir", "tests_dir")

    assert result.success is False
    assert result.coverage_pct == 0.0
    assert result.uncovered_lines == {}
    assert result.error_output == "Timeout: execução excedeu 2 minutos"

def test_run_tests_unexpected_exception(mock_subprocess_run):
    mock_subprocess_run.side_effect = Exception("unexpected error")

    result = run_tests("code_dir", "tests_dir")

    assert result.success is False
    assert result.coverage_pct == 0.0
    assert result.uncovered_lines == {}
    assert result.error_output == "unexpected error"

def test_parse_coverage_malformed_xml(mock_et_parse):
    mock_et_parse.side_effect = ET.ParseError

    result = _parse_coverage(Path("coverage.xml"))

    assert result.success is False
    assert result.coverage_pct == 0.0
    assert result.uncovered_lines == {}

def test_parse_junit_malformed_xml(mock_et_parse):
    mock_et_parse.side_effect = ET.ParseError

    passed, failed, failed_tests = _parse_junit(Path("junit.xml"))

    assert passed == 0
    assert failed == 0
    assert failed_tests == []

def test_parse_junit_no_testsuite(mock_et_parse):
    mock_et_parse.return_value.getroot.return_value.find.return_value = None

    passed, failed, failed_tests = _parse_junit(Path("junit.xml"))

    assert passed == 0
    assert failed == 0
    assert failed_tests == []