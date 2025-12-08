from omegaconf import DictConfig

from laco.language import call
from laco.keys import LAZY_CALL, LAZY_ARGS

def func_with_defaults(a: int, b: int = 10, c: str = "hello"):
    pass

def test_call_include_defaults():
    # Test with include_defaults=True
    cfg = call(func_with_defaults, include_defaults=True)()
    assert isinstance(cfg, DictConfig)
    assert cfg[LAZY_CALL] == "test_language_defaults.func_with_defaults"
    assert cfg.b == 10
    assert cfg.c == "hello"
    assert "a" not in cfg

def test_call_include_defaults_with_override():
    # Test with include_defaults=True and overriding a default
    cfg = call(func_with_defaults, include_defaults=True)(b=20, d=True)
    assert isinstance(cfg, DictConfig)
    assert cfg[LAZY_CALL] == "test_language_defaults.func_with_defaults"
    assert cfg.b == 20  # Overridden default
    assert cfg.c == "hello"
    assert cfg.d is True
    assert "a" not in cfg

def test_call_no_include_defaults():
    # Test with include_defaults=False (default behavior)
    cfg = call(func_with_defaults)()
    assert isinstance(cfg, DictConfig)
    assert cfg[LAZY_CALL] == "test_language_defaults.func_with_defaults"
    assert "b" not in cfg
    assert "c" not in cfg
    assert "a" not in cfg

def test_call_no_defaults_function():
    def func_no_defaults(x: int, y: str):
        pass

    cfg = call(func_no_defaults, include_defaults=True)()
    assert isinstance(cfg, DictConfig)
    assert cfg[LAZY_CALL] is func_no_defaults
    assert "x" not in cfg
    assert "y" not in cfg

def test_call_root_true():
    # Test with root=True to get DictConfig-like behavior
    cfg = call(func_with_defaults, include_defaults=True, root=True)() # type: ignore
    assert isinstance(cfg, DictConfig)
    assert cfg[LAZY_CALL] == "test_language_defaults.func_with_defaults"
    assert cfg.b == 10
    assert cfg.c == "hello"
    assert "a" not in cfg
