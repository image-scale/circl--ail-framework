"""Tests for ail package initialization."""


def test_version_exists():
    """Test that version is defined."""
    from ail import __version__
    assert __version__ is not None
    assert isinstance(__version__, str)
