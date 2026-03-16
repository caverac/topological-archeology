"""Tests for the hello module."""

from topo_archeo.hello import hello


def test_hello() -> None:
    """Verify hello returns the expected greeting."""
    assert hello() == "Hello from topo-archeo!"
