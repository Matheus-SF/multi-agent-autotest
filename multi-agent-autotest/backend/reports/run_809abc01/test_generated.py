import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from executor import run_tests, _parse_coverage, _parse_junit, CoverageResult

def test_run_tests_coverage_file_not_exists():
    with patch('executor.subprocess.run') as mock_run, \
         patch('executor.Path.exists', return_value=False):
        mock_run.return_value = MagicMock(stdout='output', stderr='error')
        result = run_tests('code_dir', 'tests_dir')
        assert not result.success
        assert result.coverage_pct == 0.0
        assert result.uncovered_lines == {}
        assert result.error_output == 'error'

def test_run_tests_timeout():
    with patch('executor.subprocess.run', side_effect=subprocess.TimeoutExpired(cmd='cmd', timeout=120)):
        result = run_tests('code_dir', 'tests_dir')
        assert not result.success
        assert result.coverage_pct == 0.0
        assert result.uncovered_lines == {}
        assert result.error_output == "Timeout: execução excedeu 2 minutos"

def test_run_tests_exception():
    with patch('executor.subprocess.run', side_effect=Exception('unexpected error')):
        result = run_tests('code_dir', 'tests_dir')
        assert not result.success
        assert result.coverage_pct == 0.0
        assert result.uncovered_lines == {}
        assert result.error_output == 'unexpected error'

def test_parse_coverage_malformed_xml():
    with patch('executor.ET.parse', side_effect=ET.ParseError):
        result = _parse_coverage(Path('invalid.xml'))
        assert not result.success
        assert result.coverage_pct == 0.0
        assert result.uncovered_lines == {}

def test_parse_junit_malformed_xml():
    with patch('executor.ET.parse', side_effect=ET.ParseError):
        passed, failed, failed_tests = _parse_junit(Path('invalid.xml'))
        assert passed == 0
        assert failed == 0
        assert failed_tests == []

def test_parse_junit_no_testsuite():
    with patch('executor.ET.parse') as mock_parse:
        mock_root = MagicMock()
        mock_root.find.return_value = None
        mock_parse.return_value.getroot.return_value = mock_root
        passed, failed, failed_tests = _parse_junit(Path('no_testsuite.xml'))
        assert passed == 0
        assert failed == 0
        assert failed_tests == []