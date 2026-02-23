import unittest
import os
import sys
import logging
from unittest.mock import patch, MagicMock

class LokiLoggingTestCase(unittest.TestCase):
    def setUp(self):
        # Remove app from sys.modules to force re-import and re-execution of configuration
        if 'app' in sys.modules:
            del sys.modules['app']

    def tearDown(self):
        if 'app' in sys.modules:
            del sys.modules['app']

    def test_no_loki_url(self):
        # Ensure LOKI_URL is not set
        with patch.dict(os.environ, {}, clear=True):
            # We need to make sure basic env vars required for app might need to be present if any?
            # app.py imports generation_utils which imports cqgridfinity etc.
            # Should be fine.
            import app
            handlers = app.app.logger.handlers
            # Check for LokiHandler by class name to avoid importing logging_loki here if not needed
            loki_handlers = [h for h in handlers if h.__class__.__name__ == 'LokiHandler']
            self.assertEqual(len(loki_handlers), 0)

    def test_loki_url_configured(self):
        env = {
            'LOKI_URL': 'http://mock-loki',
            'LOKI_TAGS': '{"app": "test"}',
            'LOKI_USERNAME': 'user',
            'LOKI_PASSWORD': 'pass'
        }
        with patch.dict(os.environ, env):
            with patch('logging_loki.LokiHandler') as MockLokiHandler:
                import app

                # Check if LokiHandler was initialized correctly
                MockLokiHandler.assert_called_with(
                    url='http://mock-loki',
                    tags={'app': 'test'},
                    auth=('user', 'pass'),
                    version='1'
                )

                # Check if handler was added to app.logger
                self.assertTrue(any(h == MockLokiHandler.return_value for h in app.app.logger.handlers))

    def test_invalid_tags_json(self):
        env = {
            'LOKI_URL': 'http://mock-loki',
            'LOKI_TAGS': '{invalid-json',
        }
        with patch.dict(os.environ, env):
             with patch('logging_loki.LokiHandler') as MockLokiHandler:
                import app

                # LokiHandler should NOT be instantiated because json.loads raises exception
                MockLokiHandler.assert_not_called()

                # Check that no LokiHandler was added
                handlers = app.app.logger.handlers
                loki_handlers = [h for h in handlers if h.__class__.__name__ == 'LokiHandler']
                self.assertEqual(len(loki_handlers), 0)

if __name__ == '__main__':
    unittest.main()
