import pytest

pytestmark = [pytest.mark.anyio]

PAGES = [
    (
        1,
        "Adith Jaison. Software engineer with seven years of experience as a backend developer.",
    ),
    (
        2,
        "Skills: advanced in Python and React, building secure, high-quality applications.",
    ),
    (
        3,
        "Contact: 38 Rennell Road, Liverpool. Available for interviews at your convenience.",
    ),
    (
        4,
        "Education: Master of Computer Applications (MCA), Karunya Institute of Technology.",
    ),
]


@pytest.fixture
def anyio_backend():
    return "asyncio"
