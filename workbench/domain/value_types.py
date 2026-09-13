"""Shared provider-neutral value constraints for Workbench domain records."""

from typing import Annotated, Any

from pydantic import Field


OpaqueId = Annotated[str, Field(min_length=1, max_length=255)]


class FrozenDict(dict):
    """JSON-serializable mapping that rejects in-place mutation."""

    def _immutable(self, *args, **kwargs):
        raise TypeError("immutable mapping cannot be changed")

    __setitem__ = __delitem__ = clear = pop = popitem = setdefault = update = _immutable


def freeze_value(value: Any) -> Any:
    """Recursively freeze JSON-shaped values while retaining JSON encoding."""
    if isinstance(value, dict):
        return FrozenDict({key: freeze_value(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(freeze_value(item) for item in value)
    return value
_SENSITIVE_METADATA_MARKERS = frozenset({
    "apikey", "secret", "token", "password", "credential", "authorization",
})


def _is_sensitive_key(key: object) -> bool:
    normalized = str(key).strip().casefold().replace("-", "_")
    compact = normalized.replace("_", "")
    return any(marker in compact for marker in _SENSITIVE_METADATA_MARKERS)


def assert_safe_metadata(value: Any, path: str = "metadata") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if _is_sensitive_key(key):
                raise ValueError(f"{path} cannot contain credential field: {key}")
            assert_safe_metadata(child, f"{path}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            assert_safe_metadata(child, f"{path}[{index}]")
