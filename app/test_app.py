import unittest
from app import app


class HelloWorldTestCase(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_hello_world_status_code(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

    def test_hello_world_content(self):
        response = self.client.get("/")
        self.assertIn(b"Hello World", response.data)

    def test_health_endpoint(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"ok", response.data)


if __name__ == "__main__":
    unittest.main()
