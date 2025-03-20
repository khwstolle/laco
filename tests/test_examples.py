import laco
import laco.examples.mlp
from omegaconf import DictConfig


def test_mlp_example():
    cfg = laco.load(laco.examples.mlp.__file__)
    assert isinstance(cfg, DictConfig)
    print(cfg)

    mlp = laco.instantiate(cfg.MLP)
    assert mlp is not None
    print(mlp)
