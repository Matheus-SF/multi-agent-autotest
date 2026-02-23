### test_executor.py
from unittest.mock import patch, MagicMock
import pytest
from pathlib import Path
from executor import run_tests, _parse_coverage, _parse_junit, CoverageResult

def test_run_tests_code_dir_not_exist():
    with patch('executor.subprocess.run') as mock_run:
        mock_run.side_effect = FileNotFoundError("Code directory not found")
        result = run_tests("/invalid/code_dir", "/valid/tests_dir")
        assert not result.success
        assert result.coverage_pct == 0.0
        assert result.error_output == "Code directory not found"

def test_run_tests_tests_dir_not_exist():
    with patch('executor.subprocess.run') as mock_run:
        mock_run.side_effect = FileNotFoundError("Tests directory not found")
        result = run_tests("/valid/code_dir", "/invalid/tests_dir")
        assert not result.success
        assert result.coverage_pct == 0.0
        assert result.error_output == "Tests directory not found"

def test_run_tests_timeout():
    with patch('executor.subprocess.run') as mock_run:
        mock_run.side_effect = subprocess.TimeoutExpired(cmd='docker run', timeout=120)
        result = run_tests("/valid/code_dir", "/valid/tests_dir")
        assert not result.success
        assert result.coverage_pct == 0.0
        assert result.error_output == "Timeout: execução excedeu 2 minutos"

def test_parse_coverage_file_not_exist():
    coverage_xml = Path("/invalid/coverage.xml")
    with patch('executor.ET.parse', side_effect=FileNotFoundError("Coverage XML not found")):
        result = _parse_coverage(coverage_xml)
        assert not result.success
        assert result.coverage_pct == 0.0

def test_parse_coverage_malformed_xml():
    coverage_xml = Path("/malformed/coverage.xml")
    with patch('executor.ET.parse', side_effect=ET.ParseError("Malformed XML")):
        result = _parse_coverage(coverage_xml)
        assert not result.success
        assert result.coverage_pct == 0.0

def test_parse_junit_file_not_exist():
    junit_xml = Path("/invalid/junit.xml")
    with patch('executor.ET.parse', side_effect=FileNotFoundError("JUnit XML not found")):
        passed, failed, failed_tests = _parse_junit(junit_xml)
        assert passed == 0
        assert failed == 0
        assert failed_tests == []

def test_parse_junit_malformed_xml():
    junit_xml = Path("/malformed/junit.xml")
    with patch('executor.ET.parse', side_effect=ET.ParseError("Malformed XML")):
        passed, failed, failed_tests = _parse_junit(junit_xml)
        assert passed == 0
        assert failed == 0
        assert failed_tests == []