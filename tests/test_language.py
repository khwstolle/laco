import laco
import laco.language as L
import omegaconf as O
import pytest


def target_callable[T](value: T) -> T:
    return value


@pytest.mark.parametrize("value", [True, False, None, 1, 1.0, "foo"])
def test_language_call(value):
    lc = L.call(target_callable)(value=value)

    assert isinstance(lc, O.DictConfig), type(lc)
    assert lc.value == value
    assert lc[laco.keys.LAZY_CALL] == "test_language.target_callable", lc


@pytest.mark.parametrize("value", [True, False, None, 1, 1.0, "foo"])
def test_language_partial(value):
    lc = L.partial(target_callable)()

    assert isinstance(lc, O.DictConfig), type(lc)
    assert lc[laco.keys.LAZY_CALL] == "laco.ops.partial", lc
    assert lc[laco.keys.LAZY_PART] is target_callable, lc
