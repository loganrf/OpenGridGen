import unittest
import json
import time
from unittest.mock import patch, MagicMock
from app import app
from generation_utils import GeometryValidationError

class ErrorHandlingTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_timeout_error(self):
        # Patch generate_box_task to sleep longer than timeout
        # Note: run_task_with_timeout runs in a separate process, so mocking directly might not work
        # because the function is pickled and sent to another process.
        # However, run_task_with_timeout is called in app.py.
        # We can patch run_task_with_timeout to raise TimeoutError directly.

        with patch('app.run_task_with_timeout') as mock_run:
            mock_run.side_effect = TimeoutError("Simulated timeout")

            data = {'width': 1, 'length': 1, 'height': 1}
            response = self.app.post('/api/generate_box_info',
                                     data=json.dumps(data),
                                     content_type='application/json')

            self.assertEqual(response.status_code, 408)
            res_data = json.loads(response.data)
            self.assertFalse(res_data['success'])
            self.assertEqual(res_data['error'], "Generation timed out")

    def test_validation_error(self):
        # Patch run_task_with_timeout to raise GeometryValidationError
        with patch('app.run_task_with_timeout') as mock_run:
            mock_run.side_effect = GeometryValidationError("Simulated validation error")

            data = {'width': 1, 'length': 1, 'height': 1}
            response = self.app.post('/api/generate_box_info',
                                     data=json.dumps(data),
                                     content_type='application/json')

            self.assertEqual(response.status_code, 422)
            res_data = json.loads(response.data)
            self.assertFalse(res_data['success'])
            self.assertEqual(res_data['error'], "Simulated validation error")

    def test_generic_error(self):
        # Patch run_task_with_timeout to raise generic Exception
        with patch('app.run_task_with_timeout') as mock_run:
            mock_run.side_effect = Exception("Simulated crash")

            data = {'width': 1, 'length': 1, 'height': 1}
            response = self.app.post('/api/generate_box_info',
                                     data=json.dumps(data),
                                     content_type='application/json')

            self.assertEqual(response.status_code, 500)
            res_data = json.loads(response.data)
            self.assertFalse(res_data['success'])
            self.assertEqual(res_data['error'], "Simulated crash")

if __name__ == '__main__':
    unittest.main()
