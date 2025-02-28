import builtins
import os
import typing
from contextlib import contextmanager
from uuid import uuid4

import iopathlib
import yaml
from omegaconf import DictConfig, ListConfig

__all__ = ["load_config_remote", "load_config_local"]


PATCH_PREFIX: typing.Final = "_laco_"


def load_config_remote(path: str):
    """
    Load a configuration from a remote source. Currently accepted external configuration
    sources are:

    - `Weights & Biases <https://wandb.ai/>`_ runs: ``wandb-run://<run_id>``
    """
    from unipercept.engine.integrations.wandb_integration import WANDB_RUN_PREFIX
    from unipercept.engine.integrations.wandb_integration import (
        read_run as wandb_read_run,
    )

    if path.startswith(WANDB_RUN_PREFIX):
        run = wandb_read_run(path)
        cfg = DictConfig(run.config)
    else:
        raise FileNotFoundError(path)

    return cfg


@contextmanager
def _patch_import():  # noqa: C901
    import importlib.machinery
    import importlib.util

    import_default = builtins.__import__

    def find_relative(original_file, relative_import_path, level):
        # NOTE: "from . import x" is not handled. Because then it's unclear
        # if such import should produce `x` as a python module or DictConfig.
        # This can be discussed further if needed.
        relative_import_err = (
            "Relative import of directories is not allowed within config files. "
            "Within a config file, relative import can only import other config files."
        )
        if not len(relative_import_path):
            raise ImportError(relative_import_err)

        cur_file = os.path.dirname(original_file)  # noqa: PTH120
        for _ in range(level - 1):
            cur_file = os.path.dirname(cur_file)  # noqa: PTH120
        cur_name = relative_import_path.lstrip(".")
        for part in cur_name.split("."):
            cur_file = os.path.join(cur_file, part)  # noqa: PTH118
        if not cur_file.endswith(".py"):
            cur_file += ".py"
        if not iopathlib.isfile(cur_file):
            cur_file_no_suffix = cur_file[: -len(".py")]
            if iopathlib.isdir(cur_file_no_suffix):
                raise ImportError(
                    f"Cannot import from {cur_file_no_suffix}." + relative_import_err
                )
            msg = (
                f"Cannot import name {relative_import_path} from "
                f"{original_file}: {cur_file} does not exist."
            )
            raise ImportError(msg)
        return cur_file

    def import_patched(name, globals=None, locals=None, fromlist=(), level=0):
        if (
            # Only deal with relative imports inside config files
            level != 0
            and globals is not None
            and (globals.get("__package__", "") or "").startswith(PATCH_PREFIX)
        ):
            cur_file = find_relative(globals["__file__"], name, level)
            laco.utils.check_syntax(cur_file)
            spec = importlib.machinery.ModuleSpec(
                _generate_packagename(cur_file), None, origin=cur_file
            )
            module = importlib.util.module_from_spec(spec)
            module.__file__ = cur_file
            with iopathlib.open(cur_file) as f:
                content = f.read()
            exec(compile(content, cur_file, "exec"), module.__dict__)
            for name in fromlist:  # noqa: PLR1704
                val = laco.utils.as_omegadict(module.__dict__[name])
                module.__dict__[name] = val
            return module
        return import_default(name, globals, locals, fromlist=fromlist, level=level)

    builtins.__import__ = import_patched
    yield import_patched
    builtins.__import__ = import_default


def load_config_local(path: str):
    """
    Loads a configuration from a local source.

    Users should prefer to load configurations via the unified API with
    :func:`unipercept.read_config` instead of calling this method directly.
    """
    import laco
    import laco.keys
    import laco.utils

    ext = os.path.splitext(path)[1]  # noqa: PTH122
    match ext.lower():
        case ".py":
            laco.utils.check_syntax(path)

            with _patch_import():
                # Record the filename
                nsp = {
                    "__file__": path,
                    "__package__": _generate_packagename(path),
                }
                with iopathlib.open(path) as f:
                    content = f.read()
                # Compile first with filename to:
                # 1. make filename appears in stacktrace
                # 2. make load_rel able to find its parent's (possibly remote) location
                exec(compile(content, iopathlib.get_local_path(path), "exec"), nsp)

            export = nsp.get(
                "__all__",
                (
                    k
                    for k, v in nsp.items()
                    if not k.startswith("_")
                    and (
                        isinstance(
                            v,
                            dict
                            | list
                            | DictConfig
                            | ListConfig
                            | int
                            | float
                            | str
                            | bool,
                        )
                        or v is None
                    )
                ),
            )
            obj: dict[str, typing.Any] = {k: v for k, v in nsp.items() if k in export}
            obj.setdefault(laco.keys.CONFIG_NAME, _filepath_to_name(path))
            obj.setdefault(laco.keys.CONFIG_VERSION, laco.__version__)

        case ".yaml":
            with iopathlib.open(path) as f:
                obj = yaml.unsafe_load(f)
            obj.setdefault(laco.keys.CONFIG_NAME, "unknown")
            obj.setdefault(laco.keys.CONFIG_VERSION, "unknown")
        case _:
            msg = "Unsupported file extension %s!"
            raise ValueError(msg, ext)

    return laco.utils.as_omegadict(obj)


def _filepath_to_name(path: str | iopathlib.Path) -> str | None:
    """
    Convert a file path to a module name.
    """

    configs_root = iopathlib.Path("./configs").resolve()
    path = iopathlib.Path(path).resolve()
    try:
        name = path.relative_to(configs_root).parent.as_posix() + "/" + path.stem
    except Exception:
        name = "/".join([path.parent.stem, path.stem])

    name = name.replace("./", "")
    name = name.replace("//", "/")

    if name in {"__init__", "defaults", "unknown", "config", "configs"}:
        return None
    return name.removesuffix(".py")


def _generate_packagename(path: str):
    # generate a random package name when loading config files
    return PATCH_PREFIX + str(uuid4())[:4] + "." + iopathlib.Path(path).name
