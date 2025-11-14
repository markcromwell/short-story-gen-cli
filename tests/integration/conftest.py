"""Pytest configuration for integration tests."""

import pytest
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--integration",
        action="store_true",
        default=False,
        help="Run integration tests (requires API keys and external services)",
    )
    parser.addoption(
        "--model",
        default=None,
        help="Override the integration test model (e.g., 'ollama/qwen2.5:14b')",
    )


def pytest_configure(config):
    """Configure pytest based on command line options."""
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "slow: mark test as slow running")


def pytest_collection_modifyitems(config, items):
    """Modify test collection based on markers and command line options."""
    if config.getoption("--integration"):
        # --integration given: do not skip integration tests
        return

    # Skip integration tests by default
    skip_integration = pytest.mark.skip(reason="need --integration option to run")
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip_integration)
