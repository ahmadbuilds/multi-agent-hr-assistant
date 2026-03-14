#!/usr/bin/env python
"""
Test runner script for the Multi-Agent HR Assistant project.
Provides convenient commands for running different test suites.
"""

import sys
import subprocess
import os
from pathlib import Path


class TestRunner:
    """Utility class to run tests with various configurations."""

    def __init__(self):
        """Initialize test runner."""
        self.test_dir = Path(__file__).parent
        self.project_root = self.test_dir.parent

    def run_command(self, cmd, description):
        """Run a shell command and report results."""
        print(f"\n{'=' * 60}")
        print(f"Running: {description}")
        print(f"Command: {' '.join(cmd)}")
        print(f"{'=' * 60}\n")
        
        result = subprocess.run(cmd, cwd=str(self.project_root))
        
        if result.returncode == 0:
            print(f"\n✓ {description} - PASSED")
        else:
            print(f"\n✗ {description} - FAILED")
        
        return result.returncode

    def run_all_tests(self):
        """Run all tests."""
        cmd = ["pytest", "tests/", "-v"]
        return self.run_command(cmd, "All Tests")

    def run_unit_tests(self):
        """Run only unit tests."""
        cmd = [
            "pytest",
            "tests/test_entities.py",
            "tests/test_intents.py",
            "tests/test_utilities.py",
            "-v"
        ]
        return self.run_command(cmd, "Unit Tests")

    def run_integration_tests(self):
        """Run only integration tests."""
        cmd = ["pytest", "tests/test_integration.py", "-v"]
        return self.run_command(cmd, "Integration Tests")

    def run_agent_tests(self):
        """Run only agent tests."""
        cmd = ["pytest", "tests/test_agents.py", "-v"]
        return self.run_command(cmd, "Agent Tests")

    def run_api_tests(self):
        """Run only API endpoint tests."""
        cmd = ["pytest", "tests/test_api_endpoints.py", "-v"]
        return self.run_command(cmd, "API Tests")

    def run_adapter_tests(self):
        """Run only adapter tests."""
        cmd = ["pytest", "tests/test_adapters.py", "-v"]
        return self.run_command(cmd, "Adapter Tests")

    def run_with_coverage(self):
        """Run tests with coverage report."""
        cmd = [
            "pytest",
            "tests/",
            "--cov=src/multi-agent-hr-assistant",
            "--cov-report=html",
            "--cov-report=term-missing",
            "-v"
        ]
        return self.run_command(cmd, "Tests with Coverage")

    def run_with_markers(self, marker):
        """Run tests with specific marker."""
        cmd = ["pytest", "tests/", "-m", marker, "-v"]
        return self.run_command(cmd, f"Tests with marker '{marker}'")

    def run_failed_tests(self):
        """Run only tests that failed last time."""
        cmd = ["pytest", "tests/", "--lf", "-v"]
        return self.run_command(cmd, "Last Failed Tests")

    def run_with_timeout(self, timeout=30):
        """Run tests with timeout."""
        cmd = ["pytest", "tests/", f"--timeout={timeout}", "-v"]
        return self.run_command(cmd, f"Tests with {timeout}s timeout")

    def run_parallel(self, num_workers=4):
        """Run tests in parallel."""
        cmd = ["pytest", "tests/", f"-n", str(num_workers), "-v"]
        return self.run_command(cmd, f"Parallel Tests ({num_workers} workers)")

    def run_verbose(self):
        """Run tests with verbose output."""
        cmd = ["pytest", "tests/", "-vv", "--tb=long"]
        return self.run_command(cmd, "Verbose Test Output")

    def run_html_report(self):
        """Generate HTML test report."""
        cmd = [
            "pytest",
            "tests/",
            "--html=test_report.html",
            "--self-contained-html",
            "-v"
        ]
        return self.run_command(cmd, "HTML Report Generation")

    def run_quick_smoke_tests(self):
        """Run quick smoke tests."""
        cmd = ["pytest", "tests/", "-k", "not slow", "-v", "--tb=short"]
        return self.run_command(cmd, "Smoke Tests")

    def run_specific_test(self, test_path):
        """Run a specific test file or function."""
        cmd = ["pytest", test_path, "-v"]
        return self.run_command(cmd, f"Specific Test: {test_path}")

    def run_watch_mode(self):
        """Run tests in watch mode (auto-rerun on changes)."""
        cmd = ["pytest-watch", "tests/", "--", "-v"]
        return self.run_command(cmd, "Watch Mode")

    def lint_tests(self):
        """Run linting on test files."""
        cmd = ["flake8", "tests/", "--max-line-length=100"]
        return self.run_command(cmd, "Lint Tests")


def main():
    """Main entry point."""
    runner = TestRunner()
    
    if len(sys.argv) < 2:
        print_help()
        return 0
    
    command = sys.argv[1]
    
    # Dispatch to appropriate method
    commands = {
        "all": runner.run_all_tests,
        "unit": runner.run_unit_tests,
        "integration": runner.run_integration_tests,
        "agents": runner.run_agent_tests,
        "api": runner.run_api_tests,
        "adapters": runner.run_adapter_tests,
        "coverage": runner.run_with_coverage,
        "failed": runner.run_failed_tests,
        "parallel": runner.run_parallel,
        "verbose": runner.run_verbose,
        "html": runner.run_html_report,
        "smoke": runner.run_quick_smoke_tests,
        "watch": runner.run_watch_mode,
        "lint": runner.lint_tests,
    }
    
    if command in commands:
        exit_code = commands[command]()
        return exit_code
    elif command == "marker":
        if len(sys.argv) < 3:
            print("Error: Please specify a marker")
            return 1
        marker = sys.argv[2]
        exit_code = runner.run_with_markers(marker)
        return exit_code
    elif command == "timeout":
        timeout = int(sys.argv[2]) if len(sys.argv) > 2 else 30
        exit_code = runner.run_with_timeout(timeout)
        return exit_code
    elif command == "file":
        if len(sys.argv) < 3:
            print("Error: Please specify a test file")
            return 1
        test_file = sys.argv[2]
        exit_code = runner.run_specific_test(test_file)
        return exit_code
    else:
        print(f"Unknown command: {command}")
        print_help()
        return 1


def print_help():
    """Print help message."""
    help_text = """
    Test Runner for Multi-Agent HR Assistant
    
    Usage: python run_tests.py <command> [options]
    
    Commands:
        all             Run all tests
        unit            Run only unit tests
        integration     Run only integration tests
        agents          Run only agent tests
        api             Run only API tests
        adapters        Run only adapter tests
        coverage        Run tests with coverage report
        failed          Run only last failed tests
        parallel        Run tests in parallel (4 workers)
        verbose         Run with verbose output
        html            Generate HTML test report
        smoke           Run quick smoke tests
        watch           Run in watch mode (auto-rerun)
        lint            Lint test files
        marker <name>   Run tests with specific marker
        timeout <sec>   Run tests with timeout
        file <path>     Run specific test file
        
    Examples:
        python run_tests.py all
        python run_tests.py unit
        python run_tests.py coverage
        python run_tests.py marker integration
        python run_tests.py file tests/test_entities.py
        python run_tests.py timeout 60
    """
    print(help_text)


if __name__ == "__main__":
    sys.exit(main())
