"""
Pytest configuration and shared fixtures for RPX Backend 2026 tests.
"""

import pytest
import httpx
import os
import json
from datetime import datetime
from typing import Dict, Any, Generator


class TestReporter:
    """Custom test reporter for enhanced output."""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.test_results = []
        self.endpoint_timings = []
    
    def log_test_result(self, test_name: str, status: str, duration: float, error: str = None):
        """Log a test result."""
        self.test_results.append({
            "test": test_name,
            "status": status,
            "duration": duration,
            "error": error
        })
    
    def log_endpoint_timing(self, endpoint: str, duration: float, status_code: int):
        """Log endpoint response timing."""
        self.endpoint_timings.append({
            "endpoint": endpoint,
            "duration": duration,
            "status_code": status_code
        })
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate final test report."""
        total_time = (datetime.now() - self.start_time).total_seconds()
        passed = len([r for r in self.test_results if r["status"] == "PASS"])
        failed = len([r for r in self.test_results if r["status"] == "FAIL"])
        
        # Find slow endpoints (> 1 second)
        slow_endpoints = [e for e in self.endpoint_timings if e["duration"] > 1.0]
        
        return {
            "summary": {
                "total_tests": len(self.test_results),
                "passed": passed,
                "failed": failed,
                "success_rate": f"{(passed / len(self.test_results) * 100):.1f}%" if self.test_results else "0%",
                "total_duration": f"{total_time:.2f}s"
            },
            "slow_endpoints": slow_endpoints,
            "failed_tests": [r for r in self.test_results if r["status"] == "FAIL"]
        }


@pytest.fixture(scope="session")
def test_config():
    """Test configuration fixture."""
    return {
        "base_url": os.getenv("API_BASE_URL", "http://localhost:8000"),
        "api_prefix": "/api/v1",
        "timeout": float(os.getenv("API_TIMEOUT", "10.0")),
        "skip_slow_tests": os.getenv("SKIP_SLOW_TESTS", "false").lower() == "true"
    }


@pytest.fixture(scope="session")
def http_client(test_config) -> Generator[httpx.Client, None, None]:
    """HTTP client fixture with proper cleanup."""
    with httpx.Client(
        base_url=test_config["base_url"], 
        timeout=test_config["timeout"]
    ) as client:
        yield client


@pytest.fixture(scope="session")
def reporter():
    """Test reporter fixture."""
    return TestReporter()


@pytest.fixture
def api_url(test_config):
    """Helper to construct API URLs."""
    def _api_url(endpoint: str) -> str:
        return f"{test_config['api_prefix']}{endpoint}"
    return _api_url


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "critical: marks tests as critical for basic functionality"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers."""
    for item in items:
        # Mark tests that might be slow
        if "performance" in item.nodeid or "refresh" in item.nodeid:
            item.add_marker(pytest.mark.slow)
        
        # Mark integration tests
        if "test_" in item.nodeid and any(keyword in item.nodeid.lower() 
                                         for keyword in ["endpoint", "api", "integration"]):
            item.add_marker(pytest.mark.integration)
            
        # Mark critical tests
        if any(keyword in item.nodeid.lower() 
               for keyword in ["health", "basic", "current", "config"]):
            item.add_marker(pytest.mark.critical)


@pytest.fixture
def validate_json_response():
    """Helper to validate JSON response structure."""
    def _validate(response: httpx.Response, expected_keys: list = None, expected_type: type = dict):
        """Validate JSON response."""
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text[:200]}"
        
        try:
            data = response.json()
        except json.JSONDecodeError as e:
            pytest.fail(f"Invalid JSON response: {e}")
        
        assert isinstance(data, expected_type), f"Expected {expected_type}, got {type(data)}"
        
        if expected_keys and isinstance(data, dict):
            for key in expected_keys:
                assert key in data, f"Missing key '{key}' in response"
        
        return data
    
    return _validate


@pytest.fixture
def endpoint_timer(reporter):
    """Helper to time endpoint responses."""
    def _timer(endpoint: str):
        class EndpointTimer:
            def __init__(self, endpoint: str, reporter):
                self.endpoint = endpoint
                self.reporter = reporter
                self.start_time = None
                
            def __enter__(self):
                self.start_time = datetime.now()
                return self
                
            def __exit__(self, exc_type, exc_val, exc_tb):
                if self.start_time:
                    duration = (datetime.now() - self.start_time).total_seconds()
                    # We'll set status_code in the test context if needed
                    self.reporter.log_endpoint_timing(self.endpoint, duration, 0)
        
        return EndpointTimer(endpoint, reporter)
    
    return _timer


def pytest_sessionfinish(session, exitstatus):
    """Generate final test report."""
    if hasattr(session.config, '_reporter'):
        report = session.config._reporter.generate_report()
        
        print("\n" + "="*60)
        print("RPX Backend 2026 - Test Results Summary")
        print("="*60)
        print(f"Tests: {report['summary']['total_tests']} total")
        print(f"Passed: {report['summary']['passed']}")
        print(f"Failed: {report['summary']['failed']}")  
        print(f"Success Rate: {report['summary']['success_rate']}")
        print(f"Duration: {report['summary']['total_duration']}")
        
        if report['slow_endpoints']:
            print(f"\nSlow Endpoints (>{1.0}s):")
            for endpoint in report['slow_endpoints'][:5]:  # Top 5
                print(f"  {endpoint['endpoint']}: {endpoint['duration']:.2f}s")
        
        if report['failed_tests']:
            print(f"\nFailed Tests:")
            for test in report['failed_tests'][:5]:  # Top 5
                print(f"  {test['test']}: {test['error'] or 'Unknown error'}")
        
        print("="*60)