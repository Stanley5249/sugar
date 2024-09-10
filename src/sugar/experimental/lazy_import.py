import builtins
import importlib.util as imp_util
import sys
from collections.abc import Mapping, Sequence
from types import ModuleType
from typing import Self

__all__ = ["LazyImport"]


class LazyImport:
    def __init__(self) -> None:
        self.builtins_import = builtins.__import__

    def __enter__(self) -> Self:
        builtins.__import__ = self._lazy_import
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        builtins.__import__ = self.builtins_import

    def _lazy_import(
        self,
        name: str,
        globals: Mapping[str, object] | None = None,
        locals: Mapping[str, object] | None = None,
        fromlist: Sequence[str] = (),
        level: int = 0,
    ) -> ModuleType:
        if fromlist:
            raise ImportError("lazy import does not support from-imports")

        builtins.__import__ = self.builtins_import

        try:
            spec = imp_util.find_spec(name)
            if spec is None:
                raise ModuleNotFoundError(f"no module named {name!r}")

            loader = spec.loader
            if loader is None:
                raise ImportError(f"no loader for module {name!r}")

            sys.modules[name] = module = imp_util.module_from_spec(spec)

            imp_util.LazyLoader(loader).exec_module(module)

            parent, _, child = name.rpartition(".")
            if parent:
                setattr(sys.modules[parent], child, module)
                return sys.modules[parent.partition(".")[0]]

            return module

        finally:
            builtins.__import__ = self._lazy_import
