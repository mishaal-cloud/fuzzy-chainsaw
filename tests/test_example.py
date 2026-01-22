"""Example test file."""
import pytest


def test_example():
    """Example test case."""
    assert True


def test_version():
    """Test version import."""
    from fuzzy_chainsaw import __version__

    assert __version__ == "0.1.0"
