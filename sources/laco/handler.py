import importlib.metadata
import importlib.resources
import shutil
import tempfile
import typing
from pathlib import Path as _PathlibPath
from urllib.parse import urlparse

from iopathlib.handlers import PathHandler


class LacoHandler(PathHandler):
    """PathHandler that uses a package's metadata (entry point) to get the path.

    Parameters
    ----------
    prefix : str
        The prefix to use for this path handler.
    group : str
        The name of the entry point group to use.

    """

    GROUP = "laco"
    PREFIX = "laco://"

    def __init__(self):
        self._tmp = tempfile.TemporaryDirectory()

        self.LOCAL = self._tmp.name

    def __del__(self):
        if self._tmp is not None:
            self._tmp.cleanup()

    @typing.override
    def _get_supported_prefixes(self):
        return [self.PREFIX]

    def _get_path(self, path: str, **kwargs) -> _PathlibPath:
        with importlib.resources.as_file(self._get_traversable(path)) as ph:
            if not ph.is_file():
                msg = f"File {path!r} is not a file! Got: {ph!r}"
                raise FileNotFoundError(msg)
            local_path = _PathlibPath(self.LOCAL) / path[len(self.PREFIX) :]
            local_path.parent.mkdir(parents=True, exist_ok=True)
            if local_path.exists():
                local_path.unlink()
            shutil.copy(ph, local_path)
        return local_path

    def _get_traversable(self, path: str, **kwargs) -> _PathlibPath:
        url = urlparse(path)
        assert url.scheme == self.PREFIX.rstrip("://"), (  # noqa: B005
            f"Unsupported scheme {url.scheme!r}"
        )
        pkg_available = importlib.metadata.entry_points(group=self.GROUP)
        pkg_req = url.netloc

        for pkg in pkg_available:
            if pkg.name == pkg_req:
                break
        else:
            msg = (
                f"Package {pkg_req!r} not found in group {self.GROUP!r}. "
                f"Available packages: {pkg_available}"
            )
            raise ValueError(msg)

        if ":" in pkg.value:
            pkg, fn = pkg.value.split(":", 1)

            mod = importlib.import_module(pkg)
            return getattr(mod, fn)(url.path.lstrip("/"))
        pkg_files = importlib.resources.files(pkg.value)
        return pkg_files.joinpath(url.path.lstrip("/"))

    @typing.override
    def _get_local_path(self, path: str, **kwargs):
        return str(self._get_path(path, **kwargs))

    @typing.override
    def _isfile(self, path: str, **kwargs: typing.Any) -> bool:
        return self._get_path(path, **kwargs).is_file()

    @typing.override
    def _isdir(self, path: str, **kwargs: typing.Any) -> bool:
        return self._get_path(path, **kwargs).is_dir()

    @typing.override
    def _ls(self, path: str, **kwargs: typing.Any) -> list[str]:
        msg = f"Listing directories is not supported for {self.__class__.__name__}"
        raise NotImplementedError(msg)

    @typing.override
    def _open(self, path: str, mode="r", **kwargs):
        assert "w" not in mode, (
            f"Mode {mode!r} not supported for {self.__class__.__name__}"
        )
        return self._get_traversable(path).open(mode, **kwargs)
