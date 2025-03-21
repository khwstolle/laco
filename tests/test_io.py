import json
import os

import laco
import pytest

from omegaconf import OmegaConf


@pytest.fixture()
def config():
    config = OmegaConf.create()
    config.foo = "bar"
    config.baz = 42
    config.nested = OmegaConf.create()
    config.nested.qux = "quux"
    return config


def test_dump(config):
    yaml_str = laco.dump(config)
    assert isinstance(yaml_str, str)
    print(yaml_str)

    assert "foo: bar" in yaml_str
    assert "baz: 42" in yaml_str


def test_save_load(config, tmp_path):
    # Save the config to a file
    file_path = tmp_path / "config.yaml"
    config_saved = laco.save(config, file_path, reload=False)
    assert config_saved == config, (
        "Saved config should match the original without reload"
    )
    assert file_path.is_file()

    # Write some content to the file
    with file_path.open("w") as fh:
        fh.write("xxx")
    assert file_path.read_text() == "xxx"
    
    # Override the file, and check if the new content is valid (and thus written)
    config_reload = laco.save(config, file_path, reload=True)
    assert hash(config_reload) != hash(config)
    assert file_path.is_file()
    assert file_path.read_text() != "xxx"
