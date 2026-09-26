import os
import unittest
from unittest.mock import patch

from invisible_inn.config import Config, ConfigError


class ConfigTests(unittest.TestCase):
    def test_env_file_saved_as_utf16_gives_friendly_error(self):
        bad = UnicodeDecodeError("utf-8", b"\xff\xfe", 0, 1, "invalid start byte")
        with patch("dotenv.load_dotenv", side_effect=bad):
            with self.assertRaises(ConfigError) as ctx:
                Config.from_env()
        self.assertIn("UTF-8", str(ctx.exception))

    def test_missing_token(self):
        with patch("dotenv.load_dotenv"), patch.dict(os.environ, {"DISCORD_TOKEN": ""}):
            with self.assertRaises(ConfigError):
                Config.from_env()


if __name__ == "__main__":
    unittest.main()
