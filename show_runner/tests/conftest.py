import pytest

from .support import client as client_fixture

client = pytest.fixture(client_fixture)
