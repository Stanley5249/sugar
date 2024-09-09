from pprint import PrettyPrinter
from typing import IO

from sugar._utils import AutoRepr

__all__ = ["enable"]


def enable(x: bool = True) -> bool:
    """Enable or disable the pprint hook for subclasses of AutoRepr.

    **Warning:** This might not work in all versions of Python. It relies on the private API of the pprint module.

    Args:
        enable: If True, enables the hook. If False, disables it.

    Returns:
        True if the hook is enabled, False otherwise.
    """
    _dispatch = getattr(PrettyPrinter, "_dispatch", None)
    if _dispatch is not None and isinstance(_dispatch, dict):
        if x:
            _dispatch[AutoRepr.__repr__] = _pprint_AutoRepr
            return True
        _dispatch.pop(AutoRepr.__repr__, None)
    return False


def _pprint_AutoRepr(
    self, object: AutoRepr, stream: IO[str], indent: int, allowance, context, level
) -> None:
    cls_name = object.__class__.__name__
    indent += len(cls_name) + 1
    items = object._get_auto_repr_fields()
    stream.write(f"{cls_name}(")
    self._format_namespace_items(items, stream, indent, allowance, context, level)
    stream.write(")")
