import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from dataclasses import dataclass, field


@dataclass
class CoverageResult:
    success: bool
    coverage_pct: float
    uncovered_lines: dict[str, list[int]]
    tests_passed: int = 0
    tests_failed: int = 0
    failed_tests: list = field(default_factory=list)
    error_output: str | None = None


def run_tests(code_dir: str, tests_dir: str) -> CoverageResult:
    try:
        result = subprocess.run(
            [
                "docker", "run", "--rm",
                "--network", "none",
                "--memory", "512m",
                "--cpus", "1.0",
                "-e", "PYTHONPATH=/code",
                "-v", f"{code_dir}:/code",
                "-v", f"{tests_dir}:/tests",
                "autotest-sandbox",
                "pytest", "/tests",
                "--cov=/code",
                "--cov-report=xml:/tests/coverage.xml",
                "--cov-report=html:/tests/htmlcov",
                "-v"
            ],
            capture_output=True,
            text=True,
            timeout=120
        )

        print("[Executor] stdout:", result.stdout)
        print("[Executor] stderr:", result.stderr)

        coverage_file = Path(tests_dir) / "coverage.xml"
        junit_file = Path(tests_dir) / "junit.xml"

        # Roda novamente para gerar o junit.xml
        subprocess.run(
            [
                "docker", "run", "--rm",
                "--network", "none",
                "-e", "PYTHONPATH=/code",
                "-v", f"{code_dir}:/code",
                "-v", f"{tests_dir}:/tests",
                "autotest-sandbox",
                "pytest", "/tests",
                "--junitxml=/tests/junit.xml",
                "-q"
            ],
            capture_output=True,
            text=True,
            timeout=120
        )

        coverage_exists = coverage_file.exists()
        if not coverage_exists:
            return CoverageResult(
                success=False,
                coverage_pct=0.0,
                uncovered_lines={},
                error_output=result.stderr or result.stdout
            )

        coverage_result = _parse_coverage(coverage_file)

        junit_exists = junit_file.exists()
        if junit_exists:
            passed, failed, failed_tests = _parse_junit(junit_file)
            coverage_result.tests_passed = passed
            coverage_result.tests_failed = failed
            coverage_result.failed_tests = failed_tests

        return coverage_result

    except subprocess.TimeoutExpired:
        return CoverageResult(
            success=False,
            coverage_pct=0.0,
            uncovered_lines={},
            error_output="Timeout: execução excedeu 2 minutos"
        )
    except Exception as e:
        return CoverageResult(
            success=False,
            coverage_pct=0.0,
            uncovered_lines={},
            error_output=str(e)
        )


def _parse_coverage(coverage_xml: Path) -> CoverageResult:
    try:
        tree = ET.parse(coverage_xml)
        root = tree.getroot()

        line_rate = float(root.attrib.get("line-rate", 0))
        coverage_pct = round(line_rate * 100, 2)

        uncovered_lines: dict[str, list[int]] = {}

        for package in root.iter("package"):
            for cls in package.iter("class"):
                filename = cls.attrib.get("filename", "unknown")
                missing = [
                    int(line.attrib["number"])
                    for line in cls.iter("line")
                    if line.attrib.get("hits", "0") == "0"
                ]
                if missing:
                    uncovered_lines[filename] = missing

        return CoverageResult(
            success=True,
            coverage_pct=coverage_pct,
            uncovered_lines=uncovered_lines
        )

    except Exception as e:
        return CoverageResult(
            success=False,
            coverage_pct=0.0,
            uncovered_lines={},
            error_output=str(e)
        )


def _parse_junit(junit_xml: Path) -> tuple[int, int, list[str]]:
    try:
        tree = ET.parse(junit_xml)
        root = tree.getroot()

        # Suporta tanto <testsuite> como raiz quanto <testsuites><testsuite>
        if root.tag == "testsuite":
            suite = root
        else:
            suite = root.find("testsuite")

        if suite is None:
            return 0, 0, []

        failed_tests = []
        for testcase in suite.iter("testcase"):
            failure = testcase.find("failure")
            error = testcase.find("error")
            if failure is not None or error is not None:
                name = testcase.attrib.get("name", "unknown")
                node = failure if failure is not None else error
                message = node.attrib.get("message", "")
                failed_tests.append(f"{name}: {message}")

        total = int(suite.attrib.get("tests", 0))
        failures = int(suite.attrib.get("failures", 0))
        errors = int(suite.attrib.get("errors", 0))
        failed = failures + errors
        passed = total - failed

        return passed, failed, failed_tests

    except Exception:
        return 0, 0, []