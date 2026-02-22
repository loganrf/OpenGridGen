import unittest
import json
from app import app

class OpenGridGenLidTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_lid_page(self):
        response = self.app.get('/lid')
        self.assertEqual(response.status_code, 200)

    def test_preview_lid(self):
        data = {'width': 1, 'length': 1, 'height': 0.5, 'handle_style': 'none'}
        response = self.app.post('/api/preview_lid',
                                 data=json.dumps(data),
                                 content_type='application/json')
        if response.status_code != 200 or response.mimetype != 'model/stl':
            print(f"Preview Error: {response.data}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, 'model/stl')
        self.assertIn('X-Dimensions', response.headers)
        dims = json.loads(response.headers['X-Dimensions'])
        self.assertIn('x', dims)

    def test_preview_lid_with_handle(self):
        data = {'width': 1, 'length': 1, 'height': 0.5, 'handle_style': 'simple', 'handle_height': 5.0}
        response = self.app.post('/api/preview_lid',
                                 data=json.dumps(data),
                                 content_type='application/json')
        if response.status_code != 200 or response.mimetype != 'model/stl':
            print(f"Preview Handle Error: {response.data}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, 'model/stl')

    def test_download_lid(self):
        data = {'width': 1, 'length': 1, 'height': 0.5, 'format': 'stl', 'handle_style': 'none'}
        response = self.app.post('/api/download_lid', data=data)
        if response.status_code != 200:
            print(f"Download Error: {response.data}")

        self.assertEqual(response.status_code, 200)
        self.assertIn('attachment', response.headers['Content-Disposition'])

if __name__ == '__main__':
    unittest.main()
