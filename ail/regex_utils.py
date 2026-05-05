"""
Safe regex utility module with timeout protection.

Provides pattern matching operations that can timeout to prevent
ReDoS (Regular Expression Denial of Service) attacks.
"""

import re
import signal
from multiprocessing import Process, Queue
from typing import Iterator, List, Optional, Tuple, Union


class RegexTimeoutError(Exception):
    """Raised when a regex operation exceeds the timeout."""
    pass


def escape(value: str) -> str:
    """
    Escape special regex characters in a value.

    Args:
        value: The string to escape.

    Returns:
        The escaped string safe for use in regex patterns.
    """
    return re.escape(value)


def _run_findall(queue: Queue, pattern: str, text: str) -> None:
    """Worker function to run findall in a subprocess."""
    try:
        result = re.findall(pattern, text)
        queue.put(('success', result))
    except Exception as e:
        queue.put(('error', str(e)))


def _run_finditer(queue: Queue, pattern: str, text: str) -> None:
    """Worker function to run finditer in a subprocess."""
    try:
        matches = []
        for match in re.finditer(pattern, text):
            matches.append((match.start(), match.end(), match.group()))
        queue.put(('success', matches))
    except Exception as e:
        queue.put(('error', str(e)))


def _run_match(queue: Queue, pattern: str, text: str) -> None:
    """Worker function to run match in a subprocess."""
    try:
        result = re.match(pattern, text) is not None
        queue.put(('success', result))
    except Exception as e:
        queue.put(('error', str(e)))


def _run_search(queue: Queue, pattern: str, text: str) -> None:
    """Worker function to run search in a subprocess."""
    try:
        result = re.search(pattern, text) is not None
        queue.put(('success', result))
    except Exception as e:
        queue.put(('error', str(e)))


def _execute_with_timeout(worker_func, pattern: str, text: str,
                          timeout: float, default_result):
    """
    Execute a regex operation in a subprocess with timeout.

    Args:
        worker_func: The worker function to execute.
        pattern: The regex pattern.
        text: The text to match against.
        timeout: Maximum execution time in seconds.
        default_result: Result to return on timeout or error.

    Returns:
        The result from the worker function, or default_result on timeout/error.
    """
    queue = Queue()
    process = Process(target=worker_func, args=(queue, pattern, text))

    try:
        process.start()
        process.join(timeout)

        if process.is_alive():
            # Timeout occurred
            process.terminate()
            process.join(0.1)
            if process.is_alive():
                process.kill()
                process.join(0.1)
            return default_result

        if not queue.empty():
            status, result = queue.get_nowait()
            if status == 'success':
                return result

        return default_result

    except Exception:
        return default_result
    finally:
        if process.is_alive():
            process.terminate()
            process.join(0.1)


def safe_findall(pattern: str, text: str, timeout: float = 5.0) -> List[str]:
    """
    Find all matches of a pattern in text with timeout protection.

    Args:
        pattern: The regex pattern to match.
        text: The text to search in.
        timeout: Maximum execution time in seconds. Default is 5 seconds.

    Returns:
        A list of all matches, or empty list on timeout.
    """
    return _execute_with_timeout(_run_findall, pattern, text, timeout, [])


def safe_finditer(pattern: str, text: str,
                  timeout: float = 5.0) -> List[Tuple[int, int, str]]:
    """
    Find all matches with positions in text with timeout protection.

    Args:
        pattern: The regex pattern to match.
        text: The text to search in.
        timeout: Maximum execution time in seconds. Default is 5 seconds.

    Returns:
        A list of tuples (start, end, matched_text), or empty list on timeout.
    """
    return _execute_with_timeout(_run_finditer, pattern, text, timeout, [])


def safe_match(pattern: str, text: str, timeout: float = 5.0) -> bool:
    """
    Check if pattern matches at the beginning of text with timeout protection.

    Args:
        pattern: The regex pattern to match.
        text: The text to match against.
        timeout: Maximum execution time in seconds. Default is 5 seconds.

    Returns:
        True if pattern matches at start, False otherwise or on timeout.
    """
    return _execute_with_timeout(_run_match, pattern, text, timeout, False)


def safe_search(pattern: str, text: str, timeout: float = 5.0) -> bool:
    """
    Search for pattern anywhere in text with timeout protection.

    Args:
        pattern: The regex pattern to search for.
        text: The text to search in.
        timeout: Maximum execution time in seconds. Default is 5 seconds.

    Returns:
        True if pattern is found, False otherwise or on timeout.
    """
    return _execute_with_timeout(_run_search, pattern, text, timeout, False)


def is_valid_pattern(pattern: str) -> bool:
    """
    Check if a regex pattern is valid (compiles without error).

    Args:
        pattern: The regex pattern to validate.

    Returns:
        True if the pattern is valid, False otherwise.
    """
    try:
        re.compile(pattern)
        return True
    except re.error:
        return False
