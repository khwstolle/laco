import laco
import laco.handler
import pytest


@pytest.fixture
def handler():
    return laco.handler.LacoHandler()


def test_handler(handler):
    assert handler is not None
