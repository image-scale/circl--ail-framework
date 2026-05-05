"""
Tests for the regex utility module.
"""

import pytest
import time

from ail.regex_utils import (
    safe_findall,
    safe_finditer,
    safe_match,
    safe_search,
    escape,
    is_valid_pattern,
)


class TestSafeFindall:
    """Tests for safe_findall function."""

    def test_basic_findall(self):
        """Test basic pattern matching returns all matches."""
        pattern = r'\d+'
        text = "There are 42 apples and 7 oranges"
        result = safe_findall(pattern, text)
        assert result == ['42', '7']

    def test_findall_no_match(self):
        """Test findall returns empty list when no matches."""
        pattern = r'\d+'
        text = "No numbers here"
        result = safe_findall(pattern, text)
        assert result == []

    def test_findall_with_groups(self):
        """Test findall with capture groups."""
        pattern = r'(\w+)@(\w+\.com)'
        text = "Contact us at info@example.com and support@test.com"
        result = safe_findall(pattern, text)
        assert len(result) == 2
        assert ('info', 'example.com') in result
        assert ('support', 'test.com') in result

    def test_findall_timeout_on_catastrophic_pattern(self):
        """Test findall gracefully times out on catastrophic backtracking patterns."""
        # This pattern causes catastrophic backtracking
        pattern = r'(a+)+$'
        text = 'a' * 30 + 'b'  # Doesn't match, causes backtracking

        start = time.time()
        result = safe_findall(pattern, text, timeout=0.5)
        elapsed = time.time() - start

        # Should return empty list on timeout
        assert result == []
        # Should not take much longer than timeout
        assert elapsed < 2.0


class TestSafeFinditer:
    """Tests for safe_finditer function."""

    def test_basic_finditer(self):
        """Test finditer returns match tuples with positions."""
        pattern = r'\w+'
        text = "Hello World"
        result = safe_finditer(pattern, text)

        assert len(result) == 2
        assert result[0] == (0, 5, 'Hello')
        assert result[1] == (6, 11, 'World')

    def test_finditer_no_match(self):
        """Test finditer returns empty list when no matches."""
        pattern = r'\d+'
        text = "No digits"
        result = safe_finditer(pattern, text)
        assert result == []

    def test_finditer_overlapping_positions(self):
        """Test finditer correctly reports match positions."""
        pattern = r'ab'
        text = "ab ab ab"
        result = safe_finditer(pattern, text)

        assert len(result) == 3
        assert result[0] == (0, 2, 'ab')
        assert result[1] == (3, 5, 'ab')
        assert result[2] == (6, 8, 'ab')

    def test_finditer_timeout_on_catastrophic_pattern(self):
        """Test finditer gracefully times out on catastrophic patterns."""
        pattern = r'(a+)+$'
        text = 'a' * 30 + 'b'

        start = time.time()
        result = safe_finditer(pattern, text, timeout=0.5)
        elapsed = time.time() - start

        assert result == []
        assert elapsed < 2.0


class TestSafeMatch:
    """Tests for safe_match function."""

    def test_match_at_beginning(self):
        """Test match returns True when pattern matches at start."""
        pattern = r'Hello'
        text = "Hello World"
        assert safe_match(pattern, text) is True

    def test_match_not_at_beginning(self):
        """Test match returns False when pattern is not at start."""
        pattern = r'World'
        text = "Hello World"
        assert safe_match(pattern, text) is False

    def test_match_full_string(self):
        """Test match with anchored pattern."""
        pattern = r'^\d+$'
        assert safe_match(pattern, "12345") is True
        assert safe_match(pattern, "12345abc") is False

    def test_match_timeout_on_catastrophic_pattern(self):
        """Test match gracefully times out on catastrophic patterns."""
        pattern = r'(a+)+$'
        text = 'a' * 30 + 'b'

        start = time.time()
        result = safe_match(pattern, text, timeout=0.5)
        elapsed = time.time() - start

        assert result is False
        assert elapsed < 2.0


class TestSafeSearch:
    """Tests for safe_search function."""

    def test_search_finds_pattern_anywhere(self):
        """Test search finds pattern anywhere in text."""
        pattern = r'World'
        text = "Hello World"
        assert safe_search(pattern, text) is True

    def test_search_no_match(self):
        """Test search returns False when pattern not found."""
        pattern = r'Universe'
        text = "Hello World"
        assert safe_search(pattern, text) is False

    def test_search_with_special_chars(self):
        """Test search with patterns containing special regex chars."""
        pattern = r'\$\d+\.\d{2}'
        text = "The price is $19.99"
        assert safe_search(pattern, text) is True

    def test_search_timeout_on_catastrophic_pattern(self):
        """Test search gracefully times out on catastrophic patterns."""
        pattern = r'(a+)+$'
        text = 'a' * 30 + 'b'

        start = time.time()
        result = safe_search(pattern, text, timeout=0.5)
        elapsed = time.time() - start

        assert result is False
        assert elapsed < 2.0


class TestEscape:
    """Tests for escape function."""

    def test_escape_special_chars(self):
        """Test escape properly escapes special regex characters."""
        special_chars = r'.^$*+?{}[]\|()'
        escaped = escape(special_chars)

        # The escaped string should be safe to use as a literal
        for char in special_chars:
            assert safe_search(escape(char), char) is True

    def test_escape_preserves_alphanumeric(self):
        """Test escape preserves alphanumeric characters."""
        text = "HelloWorld123"
        assert escape(text) == text

    def test_escape_special_in_context(self):
        """Test escaped string matches literally."""
        text = "file.txt"
        pattern = escape("file.txt")

        assert safe_search(pattern, text) is True
        assert safe_search(pattern, "filextxt") is False  # dot should not match any char

    def test_escape_url(self):
        """Test escape handles URLs correctly."""
        url = "https://example.com/path?query=value"
        pattern = escape(url)

        assert safe_search(pattern, url) is True
        assert safe_search(pattern, "https://example.com/pathXquery=value") is False


class TestIsValidPattern:
    """Tests for is_valid_pattern function."""

    def test_valid_patterns(self):
        """Test is_valid_pattern returns True for valid patterns."""
        valid_patterns = [
            r'\d+',
            r'[a-z]+',
            r'^hello$',
            r'(foo|bar)',
            r'\w+@\w+\.\w+',
        ]
        for pattern in valid_patterns:
            assert is_valid_pattern(pattern) is True, f"Pattern should be valid: {pattern}"

    def test_invalid_patterns(self):
        """Test is_valid_pattern returns False for invalid patterns."""
        invalid_patterns = [
            r'[',        # Unclosed bracket
            r'(',        # Unclosed group
            r'*',        # Quantifier without target
            r'?+',       # Invalid quantifier sequence
            r'[a-',      # Incomplete range
        ]
        for pattern in invalid_patterns:
            assert is_valid_pattern(pattern) is False, f"Pattern should be invalid: {pattern}"


class TestFastPatterns:
    """Tests that fast patterns complete quickly and correctly."""

    def test_email_pattern_is_fast(self):
        """Test email matching pattern completes quickly."""
        pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        text = "Contact me at user@example.com for more info"

        start = time.time()
        result = safe_findall(pattern, text, timeout=5.0)
        elapsed = time.time() - start

        assert result == ['user@example.com']
        assert elapsed < 1.0

    def test_url_pattern_is_fast(self):
        """Test URL matching pattern completes quickly."""
        pattern = r'https?://[^\s]+'
        text = "Visit https://example.com/page and http://test.org"

        start = time.time()
        result = safe_findall(pattern, text, timeout=5.0)
        elapsed = time.time() - start

        assert len(result) == 2
        assert 'https://example.com/page' in result
        assert 'http://test.org' in result
        assert elapsed < 1.0

    def test_credit_card_pattern_is_fast(self):
        """Test credit card pattern completes quickly."""
        pattern = r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b'
        text = "Card: 1234-5678-9012-3456 and 1111222233334444"

        start = time.time()
        result = safe_findall(pattern, text, timeout=5.0)
        elapsed = time.time() - start

        assert len(result) == 2
        assert elapsed < 1.0
