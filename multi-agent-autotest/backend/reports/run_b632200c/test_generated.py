from unittest.mock import patch, MagicMock
import pytest
from executor import run_tests, _parse_coverage, _parse_junit, CoverageResult
from pathlib import Path
import xml.etree.ElementTree as ET

import subprocess

def test_run_tests_coverage_file_not_exists():
    with patch('executor.subprocess.run') as mock_run, \
         patch('executor.Path.exists', side_effect=lambda p: False if 'coverage.xml' in str(p) else True):
        mock_run.return_value = MagicMock(stdout='stdout', stderr='stderr')
        result = run_tests('/fake/code_dir', '/fake/tests_dir')
        assert not result.success
        assert result.coverage_pct == 0.0
        assert result.uncovered_lines == {}
        assert result.error_output == 'stderr'

def test_run_tests_junit_file_not_exists():
    with patch('executor.subprocess.run') as mock_run, \
         patch('executor.Path.exists', side_effect=lambda p: False if 'junit.xml' in str(p) else True), \
         patch('executor._parse_coverage', return_value=CoverageResult(success=True, coverage_pct=75.0, uncovered_lines={})):
        mock_run.return_value = MagicMock(stdout='stdout', stderr='stderr')
        result = run_tests('/fake/code_dir', '/fake/tests_dir')
        assert result.success
        assert result.coverage_pct == 75.0
        assert result.uncovered_lines == {}
        assert result.tests_passed == 0
        assert result.tests_failed == 0
        assert result.failed_tests == []

def test_run_tests_timeout():
    with patch('executor.subprocess.run', side_effect=subprocess.TimeoutExpired(cmd='cmd', timeout=120)):
        result = run_tests('/fake/code_dir', '/fake/tests_dir')
        assert not result.success
        assert result.coverage_pct == 0.0
        assert result.uncovered_lines == {}
        assert result.error_output == "Timeout: execução excedeu 2 minutos"

def test_run_tests_exception():
    with patch('executor.subprocess.run', side_effect=Exception('Unexpected error')):
        result = run_tests('/fake/code_dir', '/fake/tests_dir')
        assert not result.success
        assert result.coverage_pct == 0.0
        assert result.uncovered_lines == {}
        assert result.error_output == 'Unexpected error'

def test_parse_coverage_malformed_xml():
    with patch('executor.ET.parse', side_effect=ET.ParseError):
        result = _parse_coverage(Path('/fake/coverage.xml'))
        assert not result.success
        assert result.coverage_pct == 0.0
        assert result.uncovered_lines == {}

def test_parse_junit_malformed_xml():
    with patch('executor.ET.parse', side_effect=ET.ParseError):
        passed, failed, failed_tests = _parse_junit(Path('/fake/junit.xml'))
        assert passed == 0
        assert failed == 0
        assert failed_tests == []

def test_parse_junit_no_testsuite():
    with patch('executor.ET.parse') as mock_parse:
        mock_root = MagicMock()
        mock_root.find.return_value = None
        mock_parse.return_value.getroot.return_value = mock_root
        passed, failed, failed_tests = _parse_junit(Path('/fake/junit.xml'))
        assert passed == 0
        assert failed == 0
        assert failed_tests == []