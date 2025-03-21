import laco


def test_version():
    r"""Tests whether the version attribute is set when importing the package."""

    v = laco.__version__
    assert v is not None
    assert v.lower() == v
    assert v.strip() == v
    assert isinstance(v, str)
    assert len(v) > 0
    assert v != "unknown"
