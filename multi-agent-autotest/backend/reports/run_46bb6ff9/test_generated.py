from unittest.mock import patch, mock_open
import pytest
from executor import run_tests, _parse_coverage, _parse_junit, CoverageResult
from pathlib import Path

import subprocess
import xml.etree.ElementTree as ET
from unittest.mock import patch, MagicMock

def test_run_tests_code_dir_not_exist():
    with patch('executor.subprocess.run') as mock_run, \
         patch('executor.Path.exists', return_value=False):
        result = run_tests('/invalid/code_dir', '/valid/tests_dir')
        assert not result.success
        assert result.coverage_pct == 0.0
        assert result.uncovered_lines == {}
        assert "stderr" in result.error_output or "stdout" in result.error_output

def test_run_tests_tests_dir_not_exist():
    with patch('executor.subprocess.run') as mock_run, \
         patch('executor.Path.exists', side_effect=lambda *args, **kwargs: p != Path('/valid/tests_dir/coverage.xml')):
        result = run_tests('/valid/code_dir', '/invalid/tests_dir')
        assert not result.success
        assert result.coverage_pct == 0.0
        assert result.uncovered_lines == {}
        assert "stderr" in result.error_output or "stdout" in result.error_output

def test_run_tests_timeout():
    with patch('executor.subprocess.run', side_effect=subprocess.TimeoutExpired(cmd='docker run', timeout=120)):
        result = run_tests('/valid/code_dir', '/valid/tests_dir')
        assert not result.success
        assert result.coverage_pct == 0.0
        assert result.uncovered_lines == {}
        assert result.error_output == "Timeout: execução excedeu 2 minutos"

def test_parse_coverage_file_not_exist():
    with patch('executor.ET.parse', side_effect=FileNotFoundError):
        result = _parse_coverage(Path('/invalid/coverage.xml'))
        assert not result.success
        assert result.coverage_pct == 0.0
        assert result.uncovered_lines == {}

def test_parse_coverage_malformed_xml():
    with patch('executor.ET.parse', side_effect=ET.ParseError):
        result = _parse_coverage(Path('/malformed/coverage.xml'))
        assert not result.success
        assert result.coverage_pct == 0.0
        assert result.uncovered_lines == {}

def test_parse_junit_file_not_exist():
    with patch('executor.ET.parse', side_effect=FileNotFoundError):
        passed, failed, failed_tests = _parse_junit(Path('/invalid/junit.xml'))
        assert passed == 0
        assert failed == 0
        assert failed_tests == []

def test_parse_junit_malformed_xml():
    with patch('executor.ET.parse', side_effect=ET.ParseError):
        passed, failed, failed_tests = _parse_junit(Path('/malformed/junit.xml'))
        assert passed == 0
        assert failed == 0
        assert failed_tests == []