import unittest
from pathlib import Path
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient
from main import app
from settings.dependencies import get_db

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class APITestCase(unittest.TestCase):
    """
    Base Class
    """

    def setUp(self):
        self.fake_db = AsyncMock()
        app.dependency_overrides[get_db] = lambda: self.fake_db
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()
        app.dependency_overrides.clear()
