import os

print("I AM HERE:", os.getcwd())
from modules.pdf_chatbot.embeddings import embed_texts

SKILLS = (
    "Advanced in both Python and React, building secure, high-quality applications."
)
ADDRESS = "Contact address: 38 Rennell Road, Liverpool."
EXPERIENCE = "Seven years of experience as a backend developer and technology analyst."


class TestEmbedTexts:
    def test_returns_one_vector_per_text_with_configured_size(self):
        vectors = embed_texts([SKILLS, ADDRESS, EXPERIENCE])
