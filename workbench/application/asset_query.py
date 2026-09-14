"""Query contract for Asset identities: filter, search and paginate.

A query reads the *identity* record only. Version content, checksums, storage
locations and file bytes stay behind the version read path, so a query can never
leak a payload — it answers "which assets match this filter", and nothing else.

The filter vocabulary is the domain's own closed sets (`AssetType`,
`AssetSource`, `AssetStatus`) rather than a parallel copy: two closed sets for
"what kind of asset is this" would drift the first time either gained a member,
and a query that accepted a value the domain does not define would return an
empty page forever and hide the typo. Unknown values are rejected here instead.

The record is frozen and validates on construction, so a repository can trust
every field it receives. The repository side of the contract is stated by
`AssetQueryRepository` and implemented structurally by
`SqliteAssetRepository.query_assets`; the application side is owned by
`AssetService.query`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, get_args

from workbench.domain.asset import Asset, AssetSource, AssetStatus, AssetType


DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 200
MAX_TEXT_LENGTH = 200
MAX_TAG_LENGTH = 64

_ASSET_TYPES = frozenset(get_args(AssetType))
_ASSET_SOURCES = frozenset(get_args(AssetSource))
_ASSET_STATUSES = frozenset(get_args(AssetStatus))


class AssetQueryError(ValueError):
    """A query the repository must never receive."""


def _clean_text(value: object, *, field: str, max_length: int) -> str:
    normalized = str(value or "").strip()
    if len(normalized) > max_length:
        raise AssetQueryError(f"{field} must be at most {max_length} characters")
    return normalized


def _vocabulary(values: object, allowed: frozenset[str], *, field: str) -> tuple[str, ...]:
    """Normalize a multi-select filter, rejecting anything the domain rejects."""
    selected: list[str] = []
    for value in values or ():
        item = str(value or "").strip()
        if item not in allowed:
            raise AssetQueryError(f"unknown asset {field}: {item}")
        if item not in selected:
            selected.append(item)
    return tuple(selected)


@dataclass(frozen=True)
class AssetQuery:
    """One page request against the Asset identities of one project.

    `tags` is an intersection, not a union: asking for two tags means "assets
    carrying both", which is the only reading that lets a caller narrow a
    result set by adding a filter.
    """

    project_id: str
    text: str = ""
    types: tuple[str, ...] = ()
    sources: tuple[str, ...] = ()
    statuses: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()
    limit: int = DEFAULT_PAGE_SIZE
    offset: int = 0

    def __post_init__(self) -> None:
        project_id = _clean_text(self.project_id, field="asset query project id", max_length=255)
        if not project_id:
            raise AssetQueryError("asset query requires a project id")
        object.__setattr__(self, "project_id", project_id)
        object.__setattr__(
            self, "text", _clean_text(self.text, field="asset query text", max_length=MAX_TEXT_LENGTH)
        )
        object.__setattr__(self, "types", _vocabulary(self.types, _ASSET_TYPES, field="type"))
        object.__setattr__(self, "sources", _vocabulary(self.sources, _ASSET_SOURCES, field="source"))
        object.__setattr__(self, "statuses", _vocabulary(self.statuses, _ASSET_STATUSES, field="status"))
        object.__setattr__(self, "tags", self._normalized_tags())
        object.__setattr__(self, "limit", self._page_size())
        object.__setattr__(self, "offset", self._page_offset())

    def _normalized_tags(self) -> tuple[str, ...]:
        selected: list[str] = []
        for value in self.tags or ():
            tag = _clean_text(value, field="asset query tag", max_length=MAX_TAG_LENGTH)
            if not tag:
                raise AssetQueryError("asset query tag cannot be empty")
            folded = tag.casefold()
            if folded not in selected:
                selected.append(folded)
        return tuple(selected)

    def _page_size(self) -> int:
        try:
            limit = int(self.limit)
        except (TypeError, ValueError) as error:
            raise AssetQueryError("asset query limit must be an integer") from error
        if not 1 <= limit <= MAX_PAGE_SIZE:
            raise AssetQueryError(f"asset query limit must be between 1 and {MAX_PAGE_SIZE}")
        return limit

    def _page_offset(self) -> int:
        try:
            offset = int(self.offset)
        except (TypeError, ValueError) as error:
            raise AssetQueryError("asset query offset must be an integer") from error
        if offset < 0:
            raise AssetQueryError("asset query offset must not be negative")
        return offset

    def is_filtered(self) -> bool:
        """Whether anything beyond the project scope narrows this query."""
        return bool(self.text or self.types or self.sources or self.statuses or self.tags)


@dataclass(frozen=True)
class AssetQueryPage:
    """One page of Asset identities plus the count the caller pages against."""

    items: tuple[Asset, ...]
    total: int
    limit: int
    offset: int

    @property
    def has_more(self) -> bool:
        return self.offset + len(self.items) < self.total


class AssetQueryRepository(Protocol):
    """The repository capability an Asset query needs, and nothing more."""

    def query_assets(self, query: AssetQuery) -> tuple[list[Asset], int]:
        """Return the matching page's assets and the unpaged total match count."""
