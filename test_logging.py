import unittest
import os
import json
import logging
from unittest.mock import patch
from app import app
from generation_utils import GeometryValidationError

class LoggingTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        self.log_file = 'errors.log'
        # Truncate log file or create if not exists
        with open(self.log_file, 'w') as f:
            pass

    def tearDown(self):
        # Do not remove the file to avoid messing up the file handler
        pass

    def test_logging_timeout_error(self):
        with patch('app.run_task_with_timeout') as mock_run:
            mock_run.side_effect = TimeoutError("Simulated timeout for logging")

            data = {'width': 1, 'length': 1, 'height': 1}
            self.app.post('/api/generate_box_info',
                          data=json.dumps(data),
                          content_type='application/json')

            self.assertTrue(os.path.exists(self.log_file), "errors.log should exist")
            with open(self.log_file, 'r') as f:
                content = f.read()
                self.assertIn("Generation timed out", content)

    def test_logging_validation_error(self):
        with patch('app.run_task_with_timeout') as mock_run:
            mock_run.side_effect = GeometryValidationError("Simulated validation error for logging")

            data = {'width': 1, 'length': 1, 'height': 1}
            self.app.post('/api/generate_box_info',
                          data=json.dumps(data),
                          content_type='application/json')

            self.assertTrue(os.path.exists(self.log_file), "errors.log should exist")
            with open(self.log_file, 'r') as f:
                content = f.read()
                self.assertIn("Geometry validation error: Simulated validation error for logging", content)

    def test_logging_unexpected_error(self):
        with patch('app.run_task_with_timeout') as mock_run:
            mock_run.side_effect = Exception("Simulated crash for logging")

            data = {'width': 1, 'length': 1, 'height': 1}
            self.app.post('/api/generate_box_info',
                          data=json.dumps(data),
                          content_type='application/json')

            self.assertTrue(os.path.exists(self.log_file), "errors.log should exist")
            with open(self.log_file, 'r') as f:
                content = f.read()
                self.assertIn("Unexpected error: Simulated crash for logging", content)
                self.assertIn("Traceback", content)

if __name__ == '__main__':
    unittest.main()
