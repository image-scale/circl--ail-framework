"""
Configuration management module.

Provides loading and access to application settings from INI configuration files.
Supports environment variable substitution, type conversion, and directory management.
"""

import configparser
import os
import re
from typing import Any, Dict, List, Optional, Union


class Settings:
    """
    Configuration manager that loads settings from INI files.

    Provides typed access to configuration values with support for:
    - String, integer, boolean, and list values
    - Environment variable substitution using ${VAR_NAME} syntax
    - Default values for missing keys
    - Directory path resolution and creation
    """

    def __init__(self):
        self._config: Optional[configparser.ConfigParser] = None
        self._filepath: Optional[str] = None

    def load(self, filepath: str) -> None:
        """
        Load configuration from an INI file.

        Args:
            filepath: Path to the INI configuration file.

        Raises:
            FileNotFoundError: If the config file does not exist.
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Configuration file not found: {filepath}")

        self._config = configparser.ConfigParser(interpolation=None)
        self._config.read(filepath)
        self._filepath = filepath

    def _expand_env_vars(self, value: str) -> str:
        """
        Expand environment variables in a value.

        Supports ${VAR_NAME} syntax for environment variable substitution.
        If the variable is not set, the placeholder remains unchanged.

        Args:
            value: The string value potentially containing ${VAR_NAME} placeholders.

        Returns:
            The value with environment variables expanded.
        """
        pattern = re.compile(r'\$\{([^}]+)\}')

        def replace(match):
            var_name = match.group(1)
            return os.environ.get(var_name, match.group(0))

        return pattern.sub(replace, value)

    def get_str(self, section: str, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get a string value from the configuration.

        Args:
            section: The configuration section name.
            key: The key within the section.
            default: Default value if key is not found.

        Returns:
            The string value, or default if not found.
        """
        if self._config is None:
            return default

        try:
            value = self._config.get(section, key)
            return self._expand_env_vars(value)
        except (configparser.NoSectionError, configparser.NoOptionError):
            return default

    def get_int(self, section: str, key: str, default: Optional[int] = None) -> Optional[int]:
        """
        Get an integer value from the configuration.

        Args:
            section: The configuration section name.
            key: The key within the section.
            default: Default value if key is not found.

        Returns:
            The integer value, or default if not found.

        Raises:
            ValueError: If the value cannot be converted to an integer.
        """
        value = self.get_str(section, key)
        if value is None:
            return default
        return int(value)

    def get_bool(self, section: str, key: str, default: Optional[bool] = None) -> Optional[bool]:
        """
        Get a boolean value from the configuration.

        Recognizes 'true', '1', 'yes', 'on' as True (case-insensitive).
        Recognizes 'false', '0', 'no', 'off' as False (case-insensitive).

        Args:
            section: The configuration section name.
            key: The key within the section.
            default: Default value if key is not found.

        Returns:
            The boolean value, or default if not found.

        Raises:
            ValueError: If the value is not a recognized boolean string.
        """
        value = self.get_str(section, key)
        if value is None:
            return default

        lower_value = value.lower().strip()
        if lower_value in ('true', '1', 'yes', 'on'):
            return True
        elif lower_value in ('false', '0', 'no', 'off'):
            return False
        else:
            raise ValueError(f"Cannot convert '{value}' to boolean")

    def get_list(self, section: str, key: str, default: Optional[List[str]] = None,
                 separator: str = ',') -> Optional[List[str]]:
        """
        Get a list value from the configuration.

        Parses comma-separated (or custom separator) values into a list.
        Each item is stripped of whitespace.

        Args:
            section: The configuration section name.
            key: The key within the section.
            default: Default value if key is not found.
            separator: The separator character (default: comma).

        Returns:
            A list of string values, or default if not found.
        """
        value = self.get_str(section, key)
        if value is None:
            return default

        if not value.strip():
            return []

        return [item.strip() for item in value.split(separator)]

    def get_directory(self, section: str, key: str, default: Optional[str] = None,
                      create: bool = True) -> Optional[str]:
        """
        Get a directory path from the configuration.

        Optionally creates the directory if it doesn't exist.

        Args:
            section: The configuration section name.
            key: The key within the section.
            default: Default path if key is not found.
            create: If True, create the directory if it doesn't exist.

        Returns:
            The directory path, or default if not found.
        """
        path = self.get_str(section, key, default)
        if path is None:
            return default

        # Expand user home directory
        path = os.path.expanduser(path)
        # Resolve to absolute path
        path = os.path.abspath(path)

        if create and not os.path.exists(path):
            os.makedirs(path, exist_ok=True)

        return path

    def has_section(self, section: str) -> bool:
        """
        Check if a section exists in the configuration.

        Args:
            section: The section name to check.

        Returns:
            True if the section exists, False otherwise.
        """
        if self._config is None:
            return False
        return self._config.has_section(section)

    def has_option(self, section: str, key: str) -> bool:
        """
        Check if a key exists in a section.

        Args:
            section: The section name.
            key: The key to check.

        Returns:
            True if the key exists in the section, False otherwise.
        """
        if self._config is None:
            return False
        return self._config.has_option(section, key)

    def sections(self) -> List[str]:
        """
        Get all section names in the configuration.

        Returns:
            A list of section names.
        """
        if self._config is None:
            return []
        return self._config.sections()

    def items(self, section: str) -> Dict[str, str]:
        """
        Get all key-value pairs in a section.

        Args:
            section: The section name.

        Returns:
            A dictionary of key-value pairs.
        """
        if self._config is None:
            return {}

        try:
            items = {}
            for key, value in self._config.items(section):
                items[key] = self._expand_env_vars(value)
            return items
        except configparser.NoSectionError:
            return {}


# Global settings instance for convenience
_default_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Get the default global settings instance.

    Returns:
        The default Settings instance.
    """
    global _default_settings
    if _default_settings is None:
        _default_settings = Settings()
    return _default_settings


def load_config(filepath: str) -> Settings:
    """
    Load configuration into the default global settings instance.

    Args:
        filepath: Path to the configuration file.

    Returns:
        The loaded Settings instance.
    """
    settings = get_settings()
    settings.load(filepath)
    return settings
