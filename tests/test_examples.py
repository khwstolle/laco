import laco
import laco.examples.mlp
import pytest
import torch.nn
from omegaconf import DictConfig


@pytest.mark.parametrize("num_layers", [1, 3])
def test_mlp_example(num_layers: int):
    cfg = laco.load(f"configs://examples/mlp.py?hps.num_layers={num_layers}#model")
    assert isinstance(cfg, DictConfig)

    mlp = laco.instantiate(cfg)
    assert isinstance(mlp, torch.nn.Sequential)
    print(mlp)

    mlp_input = mlp.get_submodule("input")
    assert isinstance(mlp_input, torch.nn.Sequential), mlp_input

    mlp_hidden = mlp.get_submodule("hidden")
    assert isinstance(mlp_hidden, torch.nn.Sequential), mlp_hidden
    assert len(mlp_hidden) == num_layers, mlp_hidden

    mlp_output = mlp.get_submodule("output")
    assert isinstance(mlp_output, torch.nn.Sequential), mlp_output
