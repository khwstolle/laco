import os
from math import isnan

import pytest
from laco._env import EnvFilter, get_env, strtobool


@pytest.mark.parametrize(
    ("dtype", "value"), [(str, "test"), (int, 1), (int, 0), (float, 1.0), (float, 0.0)]
)
def test_env_atomic(dtype, value):
    env = f"TEST_ENV_{dtype.__name__.upper()}_{value}"
    os.environ[env] = str(value)
    assert get_env(dtype, env) == value
    del os.environ[env]


def test_env_float_nan():
    env = "TEST_ENV_FLOAT_NAN"
    os.environ[env] = "nan"
    assert isnan(get_env(float, env))
    del os.environ[env]


def test_env_float_inf():
    env = "TEST_ENV_FLOAT_INF"
    os.environ[env] = "inf"
    assert get_env(float, env) == float("inf")
    del os.environ[env]


def test_env_float_ninf():
    env = "TEST_ENV_FLOAT_NINF"
    os.environ[env] = "-inf"
    assert get_env(float, env) == float("-inf")
    del os.environ[env]


@pytest.mark.parametrize(
    ("dtype", "value"),
    [(bool, ""), (int, "foo"), (int, ""), (float, "bar"), (float, "")],
)
def test_env_invalid(dtype, value):
    env = "TEST_ENV_FLOAT_INVALID"
    os.environ[env] = "invalid"
    with pytest.raises(ValueError):  # noqa: PT011
        get_env(float, env)
    del os.environ[env]


@pytest.mark.parametrize("value", ["True", "true", "1", "yes"])
def test_env_bool_true(value):
    env = f"TEST_ENV_BOOL_TRUE_{value}"
    os.environ[env] = value
    assert get_env(bool, env) is True
    del os.environ[env]


@pytest.mark.parametrize("value", ["False", "false", "0", "no"])
def test_env_bool_false(value):
    env = f"TEST_ENV_BOOL_FALSE_{value}"
    os.environ[env] = value
    assert get_env(bool, env) is False
    del os.environ[env]


@pytest.mark.parametrize("value", ["True", "true", "1", "yes"])
def test_strtobool_true(value):
    assert strtobool(value) is True


@pytest.mark.parametrize("value", ["False", "false", "0", "no"])
def test_strtobool_false(value):
    assert strtobool(value) is False


@pytest.mark.parametrize(
    "value",
    [
        "invalid",
        "yesno",
        "1.0",
        "TrueFalse",
        "maybe",
        "onoff",
        "truefalse",
        "yesno",
        "1.0",
    ],
)
def test_strtobool_invalid(value):
    with pytest.raises(ValueError, match="boolean value"):
        strtobool(value)


def test_envfilter_apply_string():
    assert EnvFilter.apply(EnvFilter.STRING, "test") is True
    assert EnvFilter.apply(EnvFilter.STRING, 1) is False
    assert EnvFilter.apply(EnvFilter.STRING, "") is False
    assert EnvFilter.apply(EnvFilter.STRING, None) is False


def test_envfilter_apply_none():
    assert EnvFilter.apply(None, False) is True
    assert EnvFilter.apply(None, True) is True


def test_envfilter_apply_truthy():
    assert EnvFilter.apply(EnvFilter.TRUTHY, 0.0) is False
    assert EnvFilter.apply(EnvFilter.TRUTHY, 1) is True


def test_envfilter_apply_falsy():
    assert EnvFilter.apply(EnvFilter.FALSY, 0.0) is True
    assert EnvFilter.apply(EnvFilter.FALSY, 1) is False
    assert EnvFilter.apply(EnvFilter.FALSY, None) is False


def test_envfilter_apply_positive():
    assert EnvFilter.apply(EnvFilter.POSITIVE, 0.0) is False
    assert EnvFilter.apply(EnvFilter.POSITIVE, 1) is True
    assert EnvFilter.apply(EnvFilter.POSITIVE, -1) is False


def test_envfilter_apply_negative():
    assert EnvFilter.apply(EnvFilter.NEGATIVE, 0.0) is False
    assert EnvFilter.apply(EnvFilter.NEGATIVE, 1) is False
    assert EnvFilter.apply(EnvFilter.NEGATIVE, -1) is True


def test_envfilter_apply_nonnegative():
    assert EnvFilter.apply(EnvFilter.NONNEGATIVE, 0.0) is True
    assert EnvFilter.apply(EnvFilter.NONNEGATIVE, 1) is True
    assert EnvFilter.apply(EnvFilter.NONNEGATIVE, -1) is False


def test_envfilter_apply_nonpositive():
    assert EnvFilter.apply(EnvFilter.NONPOSITIVE, 0.0) is True
    assert EnvFilter.apply(EnvFilter.NONPOSITIVE, 1) is False
    assert EnvFilter.apply(EnvFilter.NONPOSITIVE, -1) is True


def test_envfilter_apply_invalid():
    with pytest.raises(ValueError, match="filter"):
        EnvFilter.apply("invalid", 1)
    with pytest.raises(ValueError, match="filter"):
        EnvFilter.apply(42, 1)
