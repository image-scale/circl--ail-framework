"""
Tests for the configuration management module.
"""

import os
import tempfile
import pytest

from ail.config import Settings, get_settings, load_config


class TestSettings:
    """Tests for the Settings class."""

    def test_load_valid_config_file(self):
        """Test that Settings.load successfully loads an INI configuration file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
            f.write("[Database]\n")
            f.write("host = localhost\n")
            f.write("port = 5432\n")
            f.name
        try:
            settings = Settings()
            settings.load(f.name)
            assert settings.has_section("Database")
            assert settings.get_str("Database", "host") == "localhost"
        finally:
            os.unlink(f.name)

    def test_load_nonexistent_file_raises_error(self):
        """Test that loading a nonexistent config file raises FileNotFoundError."""
        settings = Settings()
        with pytest.raises(FileNotFoundError):
            settings.load("/nonexistent/path/config.ini")

    def test_get_str_returns_string_value(self):
        """Test that get_str returns the string value for a given section/key."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
            f.write("[Server]\n")
            f.write("name = production\n")
            config_path = f.name
        try:
            settings = Settings()
            settings.load(config_path)
            assert settings.get_str("Server", "name") == "production"
        finally:
            os.unlink(config_path)

    def test_get_str_nonexistent_key_returns_default(self):
        """Test that get_str with nonexistent key returns default value."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
            f.write("[Server]\n")
            f.write("name = production\n")
            config_path = f.name
        try:
            settings = Settings()
            settings.load(config_path)
            # Key doesn't exist, should return None
            assert settings.get_str("Server", "missing_key") is None
            # With explicit default
            assert settings.get_str("Server", "missing_key", "default_value") == "default_value"
            # Section doesn't exist
            assert settings.get_str("MissingSection", "key") is None
        finally:
            os.unlink(config_path)

    def test_get_int_returns_integer_value(self):
        """Test that get_int returns an integer value for a given section/key."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
            f.write("[Database]\n")
            f.write("port = 5432\n")
            f.write("connections = 100\n")
            config_path = f.name
        try:
            settings = Settings()
            settings.load(config_path)
            assert settings.get_int("Database", "port") == 5432
            assert settings.get_int("Database", "connections") == 100
            assert settings.get_int("Database", "missing", 42) == 42
        finally:
            os.unlink(config_path)

    def test_get_bool_returns_true_values(self):
        """Test that get_bool returns True for 'true', '1', 'yes'."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
            f.write("[Features]\n")
            f.write("val_true = true\n")
            f.write("val_one = 1\n")
            f.write("val_yes = yes\n")
            f.write("val_on = on\n")
            f.write("val_uppercase = TRUE\n")
            f.write("val_mixed = Yes\n")
            config_path = f.name
        try:
            settings = Settings()
            settings.load(config_path)
            assert settings.get_bool("Features", "val_true") is True
            assert settings.get_bool("Features", "val_one") is True
            assert settings.get_bool("Features", "val_yes") is True
            assert settings.get_bool("Features", "val_on") is True
            assert settings.get_bool("Features", "val_uppercase") is True
            assert settings.get_bool("Features", "val_mixed") is True
        finally:
            os.unlink(config_path)

    def test_get_bool_returns_false_values(self):
        """Test that get_bool returns False for 'false', '0', 'no'."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
            f.write("[Features]\n")
            f.write("val_false = false\n")
            f.write("val_zero = 0\n")
            f.write("val_no = no\n")
            f.write("val_off = off\n")
            f.write("val_uppercase = FALSE\n")
            config_path = f.name
        try:
            settings = Settings()
            settings.load(config_path)
            assert settings.get_bool("Features", "val_false") is False
            assert settings.get_bool("Features", "val_zero") is False
            assert settings.get_bool("Features", "val_no") is False
            assert settings.get_bool("Features", "val_off") is False
            assert settings.get_bool("Features", "val_uppercase") is False
        finally:
            os.unlink(config_path)

    def test_get_bool_with_default(self):
        """Test that get_bool returns default for missing keys."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
            f.write("[Features]\n")
            config_path = f.name
        try:
            settings = Settings()
            settings.load(config_path)
            assert settings.get_bool("Features", "missing") is None
            assert settings.get_bool("Features", "missing", True) is True
            assert settings.get_bool("Features", "missing", False) is False
        finally:
            os.unlink(config_path)

    def test_get_list_parses_comma_separated_values(self):
        """Test that get_list parses comma-separated values into a list."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
            f.write("[Servers]\n")
            f.write("hosts = server1, server2, server3\n")
            f.write("ports = 80,443,8080\n")
            f.write("empty = \n")
            config_path = f.name
        try:
            settings = Settings()
            settings.load(config_path)

            hosts = settings.get_list("Servers", "hosts")
            assert hosts == ["server1", "server2", "server3"]

            ports = settings.get_list("Servers", "ports")
            assert ports == ["80", "443", "8080"]

            empty = settings.get_list("Servers", "empty")
            assert empty == []

            missing = settings.get_list("Servers", "missing")
            assert missing is None

            default = settings.get_list("Servers", "missing", ["default"])
            assert default == ["default"]
        finally:
            os.unlink(config_path)

    def test_environment_variable_expansion(self):
        """Test that ${ENV_VAR} in config values are replaced by environment variable values."""
        # Set test environment variable
        os.environ["TEST_AIL_DB_HOST"] = "db.example.com"
        os.environ["TEST_AIL_DB_PORT"] = "3306"

        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
            f.write("[Database]\n")
            f.write("host = ${TEST_AIL_DB_HOST}\n")
            f.write("port = ${TEST_AIL_DB_PORT}\n")
            f.write("url = jdbc://${TEST_AIL_DB_HOST}:${TEST_AIL_DB_PORT}/mydb\n")
            f.write("unchanged = ${NONEXISTENT_VAR}\n")
            config_path = f.name
        try:
            settings = Settings()
            settings.load(config_path)

            # Single env var
            assert settings.get_str("Database", "host") == "db.example.com"
            assert settings.get_int("Database", "port") == 3306

            # Multiple env vars in one value
            assert settings.get_str("Database", "url") == "jdbc://db.example.com:3306/mydb"

            # Nonexistent env var remains unchanged
            assert settings.get_str("Database", "unchanged") == "${NONEXISTENT_VAR}"
        finally:
            os.unlink(config_path)
            del os.environ["TEST_AIL_DB_HOST"]
            del os.environ["TEST_AIL_DB_PORT"]

    def test_get_directory_creates_directory(self):
        """Test that get_directory returns the path and creates directory if it does not exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_content = f"[Directories]\ndata = {tmpdir}/new_data_dir\n"
            config_path = os.path.join(tmpdir, "config.ini")
            with open(config_path, 'w') as f:
                f.write(config_content)

            settings = Settings()
            settings.load(config_path)

            data_dir = settings.get_directory("Directories", "data")

            # Directory should be created
            assert os.path.exists(data_dir)
            assert os.path.isdir(data_dir)
            expected_path = os.path.abspath(os.path.join(tmpdir, "new_data_dir"))
            assert data_dir == expected_path

    def test_get_directory_without_create(self):
        """Test get_directory with create=False doesn't create directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            new_dir = os.path.join(tmpdir, "nonexistent_dir")
            config_content = f"[Directories]\ndata = {new_dir}\n"
            config_path = os.path.join(tmpdir, "config.ini")
            with open(config_path, 'w') as f:
                f.write(config_content)

            settings = Settings()
            settings.load(config_path)

            data_dir = settings.get_directory("Directories", "data", create=False)

            # Directory should NOT be created
            assert not os.path.exists(new_dir)
            assert data_dir == os.path.abspath(new_dir)

    def test_has_section(self):
        """Test has_section method."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
            f.write("[Existing]\nkey = value\n")
            config_path = f.name
        try:
            settings = Settings()
            settings.load(config_path)
            assert settings.has_section("Existing") is True
            assert settings.has_section("NonExisting") is False
        finally:
            os.unlink(config_path)

    def test_has_option(self):
        """Test has_option method."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
            f.write("[Section]\nexisting_key = value\n")
            config_path = f.name
        try:
            settings = Settings()
            settings.load(config_path)
            assert settings.has_option("Section", "existing_key") is True
            assert settings.has_option("Section", "missing_key") is False
        finally:
            os.unlink(config_path)

    def test_sections(self):
        """Test sections method."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
            f.write("[First]\nkey = value\n")
            f.write("[Second]\nkey = value\n")
            f.write("[Third]\nkey = value\n")
            config_path = f.name
        try:
            settings = Settings()
            settings.load(config_path)
            sections = settings.sections()
            assert "First" in sections
            assert "Second" in sections
            assert "Third" in sections
            assert len(sections) == 3
        finally:
            os.unlink(config_path)

    def test_items(self):
        """Test items method."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
            f.write("[Database]\n")
            f.write("host = localhost\n")
            f.write("port = 5432\n")
            config_path = f.name
        try:
            settings = Settings()
            settings.load(config_path)
            items = settings.items("Database")
            assert items["host"] == "localhost"
            assert items["port"] == "5432"

            # Non-existing section returns empty dict
            assert settings.items("NonExisting") == {}
        finally:
            os.unlink(config_path)


class TestGlobalSettings:
    """Tests for global settings functions."""

    def test_get_settings_returns_singleton(self):
        """Test that get_settings returns the same instance."""
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2

    def test_load_config_loads_and_returns_settings(self):
        """Test that load_config loads the file and returns settings."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
            f.write("[App]\nname = test_app\n")
            config_path = f.name
        try:
            settings = load_config(config_path)
            assert settings.get_str("App", "name") == "test_app"
        finally:
            os.unlink(config_path)
