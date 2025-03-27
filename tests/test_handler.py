import laco
import laco.handler
import pytest


@pytest.fixture(scope="module")
def handler():
    return laco.handler.ConfigsPathHandler()


@pytest.mark.parametrize(
    "path", ["configs://examples/mlp.py"]
)
def test_resolve(handler, path: str):
    assert handler is not None
    assert len(path) > 0
    assert path.startswith("configs://")

    file = handler._locate(path)
    print(f"{path} -> {file}")
    assert file is not None
    assert file.exists()

    ext = path.split(".")[-1]
    assert file.name.endswith(ext)
