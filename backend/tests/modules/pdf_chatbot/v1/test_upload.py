from urllib import response

from tests.base import FIXTURES_DIR, APITestCase

UPLOAD_URL = "/api/v1/pdf_chatbot/upload"


class TestUploadEndPoint(APITestCase):

    @classmethod
    def setUpClass(cls):
        cls.pdf_bytes = (FIXTURES_DIR / "sample.pdf").read_bytes()

    def upload(self, filename, content, content_type):
        return self.client.post(
            UPLOAD_URL, files={"file": (filename, content, content_type)}
        )

    def test_valid_pdf_returns_200_with_document(self):
        response = self.upload("sample.pdf", self.pdf_bytes, "application/pdf")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["filename"], "sample.pdf")
        self.assertEqual(body["mime_type"], "application/pdf")
        self.assertEqual(body["status"], "UPLOADED")
