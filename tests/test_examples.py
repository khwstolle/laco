import pathlib

import laco
import laco.examples.mlp
import torch.nn
from omegaconf import DictConfig


def test_mlp_example():
    cfg = laco.load(pathlib.Path(laco.__file__).parent / "examples" / "mlp.py")
    assert isinstance(cfg, DictConfig)
    print(cfg)

    mlp = laco.instantiate(cfg.MLP)
    assert isinstance(mlp, torch.nn.Sequential)
    print(mlp)
