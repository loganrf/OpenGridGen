import unittest
import json
from app import app

class OpenGridGenTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_index(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)

    def test_box_page(self):
        response = self.app.get('/box')
        self.assertEqual(response.status_code, 200)

    def test_baseplate_page(self):
        response = self.app.get('/baseplate')
        self.assertEqual(response.status_code, 200)

    def test_generate_box_info(self):
        data = {'width': 2, 'length': 3, 'height': 2}
        response = self.app.post('/api/generate_box_info',
                                 data=json.dumps(data),
                                 content_type='application/json')
        self.assertEqual(response.status_code, 200)
        res_data = json.loads(response.data)
        self.assertTrue(res_data['success'])
        self.assertIn('dimensions', res_data)

    def test_preview_box(self):
        data = {'width': 1, 'length': 1, 'height': 2}
        response = self.app.post('/api/preview_box',
                                 data=json.dumps(data),
                                 content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, 'model/stl')
        self.assertIn('X-Dimensions', response.headers)
        dims = json.loads(response.headers['X-Dimensions'])
        self.assertIn('x', dims)

    def test_download_box(self):
        data = {'width': 1, 'length': 1, 'height': 2, 'format': 'stl'}
        response = self.app.post('/api/download_box', data=data)
        self.assertEqual(response.status_code, 200)
        self.assertIn('attachment', response.headers['Content-Disposition'])

    def test_generate_baseplate_info(self):
        data = {'width': 2, 'length': 2}
        response = self.app.post('/api/generate_baseplate_info',
                                 data=json.dumps(data),
                                 content_type='application/json')
        self.assertEqual(response.status_code, 200)
        res_data = json.loads(response.data)
        self.assertTrue(res_data['success'])

    def test_preview_baseplate(self):
        data = {'width': 1, 'length': 1}
        response = self.app.post('/api/preview_baseplate',
                                 data=json.dumps(data),
                                 content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, 'model/stl')
        self.assertIn('X-Dimensions', response.headers)
        dims = json.loads(response.headers['X-Dimensions'])
        self.assertIn('x', dims)

    def test_download_baseplate(self):
        data = {'width': 1, 'length': 1, 'format': 'step'}
        response = self.app.post('/api/download_baseplate', data=data)
        self.assertEqual(response.status_code, 200)
        self.assertIn('attachment', response.headers['Content-Disposition'])

if __name__ == '__main__':
    unittest.main()
