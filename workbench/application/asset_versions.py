"""Read contract for one Asset's version history.

An Asset's identity record names its versions by id and deliberately carries no
rule about which of them is current, because "which version is current" is a
fact about the *sequence*, not about the identity. A version record knows its
own content address, checksum, provenance and creation time but cannot see its
siblings, so it cannot order itself either. The history is the one place those
two facts meet: the versions of one asset, in sequence, with the end of the
sequence named as the current version.

Ordinal is the position the repository assigns — `create_version` rejects any
ordinal that is not `count + 1` — so a stored sequence is gap-free and starts at
1 by construction. This record *asserts* that instead of assuming it: a
"history" with a duplicate or a gap is not a history, and saying so here is what
makes the sequence a testable claim rather than a comment.

Ordering is derived from the ordinals and never trusted from the caller, so a
repository that returns rows in any order still yields the one correct history.
`current` is derived the same way, from the sequence rather than from a stored
flag: a stored flag would be a second owner for a fact the sequence already
carries, and the two could disagree.

The record is frozen because `AssetService.history` returns it to a transport
that reads it more than once (the response body and the current-version id); a
record able to change between those reads would describe two different
histories.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from workbench.domain.asset import AssetVersion


class AssetVersionHistoryError(ValueError):
    """A set of versions that cannot be one Asset's history."""


@dataclass(frozen=True)
class AssetVersionHistory:
    """One Asset's versions, in ordinal order, with the current one resolved."""

    asset_id: str
    versions: tuple[AssetVersion, ...] = ()

    def __post_init__(self) -> None:
        asset_id = str(self.asset_id or "").strip()
        if not asset_id:
            raise AssetVersionHistoryError("asset version history requires an asset id")
        object.__setattr__(self, "asset_id", asset_id)

        versions = tuple(self.versions or ())
        for version in versions:
            if not isinstance(version, AssetVersion):
                raise AssetVersionHistoryError(
                    "asset version history takes AssetVersion records"
                )
            if version.asset_id != asset_id:
                raise AssetVersionHistoryError(
                    f"version {version.id} belongs to asset {version.asset_id}, not {asset_id}"
                )

        ordered = tuple(sorted(versions, key=lambda version: version.ordinal))
        ordinals = [version.ordinal for version in ordered]
        if len(set(ordinals)) != len(ordinals):
            raise AssetVersionHistoryError("asset version ordinals must be unique")
        if ordinals and ordinals != list(range(1, len(ordinals) + 1)):
            raise AssetVersionHistoryError(
                "asset version ordinals must be a gap-free sequence from 1"
            )
        object.__setattr__(self, "versions", ordered)

    @property
    def current(self) -> AssetVersion | None:
        """The version the sequence ends at, or None when the asset has none."""
        return self.versions[-1] if self.versions else None

    @property
    def current_version_id(self) -> str | None:
        current = self.current
        return current.id if current is not None else None

    def version(self, version_id: str) -> AssetVersion | None:
        """The named version, or None when this history does not contain it."""
        wanted = str(version_id or "").strip()
        for version in self.versions:
            if version.id == wanted:
                return version
        return None

    def __len__(self) -> int:
        return len(self.versions)


class AssetVersionHistoryRepository(Protocol):
    """The repository capability a version history needs, and nothing more."""

    def list_versions(self, asset_id: str) -> list[AssetVersion]:
        """Return every version of one asset, in ordinal order."""
