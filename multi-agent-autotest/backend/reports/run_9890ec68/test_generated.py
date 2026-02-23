from unittest import mock
import pytest
from pathlib import Path
from executor import run_tests, _parse_coverage, _parse_junit, CoverageResult

import subprocess
import xml.etree.ElementTree as ET
from unittest.mock import patch, MagicMock

def test_run_tests_coverage_file_not_exists():
    with mock.patch('executor.subprocess.run') as mock_run, \
         mock.patch('executor.Path.exists', side_effect=lambda *args, **kwargs: False if "coverage.xml" in str(args[0]) else True):
        mock_run.return_value.stdout = "stdout"
        mock_run.return_value.stderr = "stderr"
        result = run_tests("/fake/code_dir", "/fake/tests_dir")
        assert not result.success
        assert result.coverage_pct == 0.0
        assert result.uncovered_lines == {}
        assert result.error_output == "stderr"

def test_run_tests_junit_file_not_exists():
    with mock.patch('executor.subprocess.run') as mock_run, \
         mock.patch('executor.Path.exists', side_effect=lambda *args, **kwargs: False if "junit.xml" in str(args[0]) else True), \
         mock.patch('executor._parse_coverage', return_value=CoverageResult(True, 75.0, {})):
        result = run_tests("/fake/code_dir", "/fake/tests_dir")
        assert result.success
        assert result.coverage_pct == 75.0
        assert result.tests_passed == 0
        assert result.tests_failed == 0
        assert result.failed_tests == []

def test_run_tests_timeout():
    with mock.patch('executor.subprocess.run', side_effect=subprocess.TimeoutExpired(cmd='cmd', timeout=120)):
        result = run_tests("/fake/code_dir", "/fake/tests_dir")
        assert not result.success
        assert result.coverage_pct == 0.0
        assert result.uncovered_lines == {}
        assert result.error_output == "Timeout: execução excedeu 2 minutos"

def test_run_tests_unexpected_exception():
    with mock.patch('executor.subprocess.run', side_effect=Exception("Unexpected error")):
        result = run_tests("/fake/code_dir", "/fake/tests_dir")
        assert not result.success
        assert result.coverage_pct == 0.0
        assert result.uncovered_lines == {}
        assert result.error_output == "Unexpected error"

def test_parse_coverage_file_not_exists():
    with mock.patch('executor.ET.parse', side_effect=FileNotFoundError):
        result = _parse_coverage(Path("/fake/coverage.xml"))
        assert not result.success
        assert result.coverage_pct == 0.0
        assert result.uncovered_lines == {}

def test_parse_coverage_malformed_xml():
    with mock.patch('executor.ET.parse', side_effect=ET.ParseError):
        result = _parse_coverage(Path("/fake/coverage.xml"))
        assert not result.success
        assert result.coverage_pct == 0.0
        assert result.uncovered_lines == {}

def test_parse_junit_file_not_exists():
    with mock.patch('executor.ET.parse', side_effect=FileNotFoundError):
        passed, failed, failed_tests = _parse_junit(Path("/fake/junit.xml"))
        assert passed == 0
        assert failed == 0
        assert failed_tests == []

def test_parse_junit_malformed_xml():
    with mock.patch('executor.ET.parse', side_effect=ET.ParseError):
        passed, failed, failed_tests = _parse_junit(Path("/fake/junit.xml"))
        assert passed == 0
        assert failed == 0
        assert failed_tests == []