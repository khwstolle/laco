
import pytest
from omegaconf import OmegaConf

from laco._overrides import apply_overrides


def test_delete_override():
    cfg = OmegaConf.create({"a": {"b": 1}, "c": 2})
    overrides = ["~a.b"]
    with pytest.raises(NotImplementedError):
        apply_overrides(cfg, overrides)
