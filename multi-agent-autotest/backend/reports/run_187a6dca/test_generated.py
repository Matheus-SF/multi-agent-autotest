from unittest.mock import patch, MagicMock
import pytest
from pathlib import Path
from executor import run_tests, _parse_coverage, _parse_junit, CoverageResult

def test_run_tests_coverage_file_not_exists():
    with patch('executor.subprocess.run') as mock_run, \
         patch('executor.Path.exists', return_value=False):
        mock_run.return_value.stdout = "stdout"
        mock_run.return_value.stderr = "stderr"
        
        result = run_tests("code_dir", "tests_dir")
        
        assert not result.success
        assert result.coverage_pct == 0.0
        assert result.uncovered_lines == {}
        assert result.error_output == "stderr"

def test_run_tests_timeout():
    with patch('executor.subprocess.run', side_effect=subprocess.TimeoutExpired(cmd='cmd', timeout=120)):
        result = run_tests("code_dir", "tests_dir")
        
        assert not result.success
        assert result.coverage_pct == 0.0
        assert result.uncovered_lines == {}
        assert result.error_output == "Timeout: execução excedeu 2 minutos"

def test_run_tests_general_exception():
    with patch('executor.subprocess.run', side_effect=Exception("General Error")):
        result = run_tests("code_dir", "tests_dir")
        
        assert not result.success
        assert result.coverage_pct == 0.0
        assert result.uncovered_lines == {}
        assert result.error_output == "General Error"

def test_parse_coverage_file_not_exists():
    with patch('executor.ET.parse', side_effect=FileNotFoundError):
        result = _parse_coverage(Path("non_existent_file.xml"))
        
        assert not result.success
        assert result.coverage_pct == 0.0
        assert result.uncovered_lines == {}

def test_parse_coverage_malformed_xml():
    with patch('executor.ET.parse', side_effect=ET.ParseError):
        result = _parse_coverage(Path("malformed.xml"))
        
        assert not result.success
        assert result.coverage_pct == 0.0
        assert result.uncovered_lines == {}

def test_parse_junit_file_not_exists():
    with patch('executor.ET.parse', side_effect=FileNotFoundError):
        passed, failed, failed_tests = _parse_junit(Path("non_existent_file.xml"))
        
        assert passed == 0
        assert failed == 0
        assert failed_tests == []

def test_parse_junit_malformed_xml():
    with patch('executor.ET.parse', side_effect=ET.ParseError):
        passed, failed, failed_tests = _parse_junit(Path("malformed.xml"))
        
        assert passed == 0
        assert failed == 0
        assert failed_tests == []