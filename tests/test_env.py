import os
from math import isnan

import pytest
from laco._env import get_env


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
    with pytest.raises(ValueError):
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
