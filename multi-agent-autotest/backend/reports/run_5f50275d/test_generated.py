# test_executor.py

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from executor import run_tests, _parse_coverage, _parse_junit, CoverageResult

# Testes para a função run_tests
import subprocess
import xml.etree.ElementTree as ET

@patch('executor.subprocess.run')
@patch('executor.Path.exists')
def test_run_tests_happy_path(mock_exists, mock_run):
    mock_exists.return_value = True
    mock_run.return_value = MagicMock(stdout="stdout", stderr="stderr")

    with patch('executor._parse_coverage', return_value=CoverageResult(success=True, coverage_pct=75.0, uncovered_lines={})):
        with patch('executor._parse_junit', return_value=(10, 2, ['test_fail'])):
            result = run_tests('/fake/code', '/fake/tests')
            assert result.success
            assert result.coverage_pct == 75.0
            assert result.tests_passed == 10
            assert result.tests_failed == 2
            assert result.failed_tests == ['test_fail']

@patch('executor.subprocess.run')
@patch('executor.Path.exists')
def test_run_tests_coverage_file_missing(mock_exists, mock_run):
    mock_exists.side_effect = lambda p: p.name != 'coverage.xml'
    mock_run.return_value = MagicMock(stdout="stdout", stderr="stderr")

    result = run_tests('/fake/code', '/fake/tests')
    assert not result.success
    assert result.coverage_pct == 0.0
    assert 'stderr' in result.error_output

@patch('executor.subprocess.run')
def test_run_tests_timeout(mock_run):
    mock_run.side_effect = subprocess.TimeoutExpired(cmd='docker', timeout=120)

    result = run_tests('/fake/code', '/fake/tests')
    assert not result.success
    assert result.coverage_pct == 0.0
    assert 'Timeout' in result.error_output

@patch('executor.subprocess.run')
def test_run_tests_unexpected_exception(mock_run):
    mock_run.side_effect = Exception("Unexpected error")

    result = run_tests('/fake/code', '/fake/tests')
    assert not result.success
    assert result.coverage_pct == 0.0
    assert 'Unexpected error' in result.error_output

# Testes para a função _parse_coverage
@patch('executor.ET.parse')
def test_parse_coverage_happy_path(mock_parse):
    mock_tree = MagicMock()
    mock_root = MagicMock()
    mock_root.attrib = {'line-rate': '0.75'}
    mock_tree.getroot.return_value = mock_root
    mock_parse.return_value = mock_tree

    result = _parse_coverage(Path('/fake/coverage.xml'))
    assert result.success
    assert result.coverage_pct == 75.0

@patch('executor.ET.parse')
def test_parse_coverage_malformed_xml(mock_parse):
    mock_parse.side_effect = ET.ParseError

    result = _parse_coverage(Path('/fake/coverage.xml'))
    assert not result.success
    assert result.coverage_pct == 0.0

# Testes para a função _parse_junit
@patch('executor.ET.parse')
def test_parse_junit_happy_path(mock_parse):
    mock_tree = MagicMock()
    mock_root = MagicMock()
    mock_suite = MagicMock()
    mock_suite.attrib = {'tests': '10', 'failures': '2', 'errors': '0'}
    mock_root.find.return_value = mock_suite
    mock_tree.getroot.return_value = mock_root
    mock_parse.return_value = mock_tree

    passed, failed, failed_tests = _parse_junit(Path('/fake/junit.xml'))
    assert passed == 8
    assert failed == 2
    assert failed_tests == []

@patch('executor.ET.parse')
def test_parse_junit_malformed_xml(mock_parse):
    mock_parse.side_effect = ET.ParseError

    passed, failed, failed_tests = _parse_junit(Path('/fake/junit.xml'))
    assert passed == 0
    assert failed == 0
    assert failed_tests == []