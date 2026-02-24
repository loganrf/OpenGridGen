import unittest
import sys
import logging
from unittest.mock import patch

class LokiLoggingTestCase(unittest.TestCase):
    def setUp(self):
        # Remove app from sys.modules to force re-import and re-execution of configuration
        if 'app' in sys.modules:
            del sys.modules['app']

    def tearDown(self):
        if 'app' in sys.modules:
            del sys.modules['app']

    def test_loki_handler_configured(self):
        with patch('logging_loki.LokiHandler') as MockLokiHandler:
            import app

            # Check if LokiHandler was initialized with expected values
            MockLokiHandler.assert_called_with(
                url="http://192.168.1.223:3100/loki/api/v1/push",
                tags={"application": "opengridgen"},
                version="1"
            )

            # Check if handler was added to app.logger
            # Since MockLokiHandler() returns a mock instance, we check if that instance is in handlers
            # However, app.py instantiates it at module level.
            # MockLokiHandler is the class (mocked).
            # The instance created is MockLokiHandler.return_value.

            self.assertTrue(any(h == MockLokiHandler.return_value for h in app.app.logger.handlers))

            # Check logger level
            self.assertEqual(app.app.logger.level, logging.INFO)

if __name__ == '__main__':
    unittest.main()
