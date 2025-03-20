import laco
import laco.examples.mlp
import torch.nn
from omegaconf import DictConfig


def test_mlp_example():
    cfg = laco.load(laco.examples.mlp.__file__)
    assert isinstance(cfg, DictConfig)
    print(cfg)

    mlp = laco.instantiate(cfg.MLP)
    assert isinstance(mlp, torch.nn.Sequential)
    print(mlp)
