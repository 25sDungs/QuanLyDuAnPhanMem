import unittest
from index import app

class TestHealthFlaskApp(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_health_check(self):
        response = self.client.get('/health')
        print(f"Status code: {response.status_code}")
        print(f"Response data: {response.data}")
        # Sau đó mới assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"status": "healthy"})