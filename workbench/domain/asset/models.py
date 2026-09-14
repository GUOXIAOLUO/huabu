"""Asset identity for external/input resources, kept apart from its versions.

An Asset is the stable identity of one *input* resource: something brought into a
project from outside, never produced by an execution. It answers *which* resource
this is — which project owns it, where it came from, what kind of thing it is and
what state it is in — and nothing else.

What the resource *is* at any point in time belongs to its versions. The Asset
therefore names versions by id and carries no content, no checksum, no storage
location and no rule about which version is current: a reference that also held
the content would give the same fact two owners, and editing a version would
become an edit of the Asset. Which is why the identity record below is the only
place an Asset's identity is defined, and why it is frozen.
"""

from datetime import datetime
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from workbench.domain.value_types import OpaqueId, assert_safe_metadata, freeze_value


ASSET_SCHEMA_VERSION = "workbench.asset/1"

# Where one Asset came from. Every one of these is an entry into the project from
# outside it; a resource produced inside the project is an Artifact, not an Asset.
AssetSource = Literal[
    "upload",  # a file the user pushed into the project
    "url",  # a remote address the project reads through
    "local_path",  # a file that already existed on disk
    "provider",  # pulled through an external provider connection
    "import",  # brought in from another library or pack
    "execution",  # explicitly saved from a selected Workbench result
]

AssetType = Literal[
    "image",
    "video",
    "audio",
    "document",
    "model",
    "workflow",
    "other",
]

# Lifecycle state of the identity itself. Which states a set of versions permits
# is a versioning rule and belongs to the version record, not here.
AssetStatus = Literal["draft", "ready", "archived"]


class Asset(BaseModel):
    """The identity of one external/input resource and the versions it names."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal[ASSET_SCHEMA_VERSION] = ASSET_SCHEMA_VERSION
    id: OpaqueId
    project_id: OpaqueId
    source: AssetSource
    type: AssetType
    status: AssetStatus = "draft"
    version_ids: tuple[OpaqueId, ...] = ()
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def require_distinct_version_ids(self) -> "Asset":
        if len(set(self.version_ids)) != len(self.version_ids):
            raise ValueError("asset version ids must be unique")
        return self

    @model_validator(mode="after")
    def freeze_metadata(self) -> "Asset":
        # Same treatment the other canonical records give theirs: a frozen record
        # with a mutable interior is not frozen, and a credential in metadata is
        # a credential in a record that gets persisted and logged.
        assert_safe_metadata(self.metadata, path="metadata")
        object.__setattr__(self, "metadata", freeze_value(self.metadata))
        return self

    def with_version(self, version_id: str) -> "Asset":
        """Return a new Asset naming one more version; the identity is unchanged.

        Versions are appended and never rewritten here: a version already named
        by this Asset stays named by it, and nothing about the version itself can
        be changed through this record. Re-validating the whole record (rather
        than copying it) is what keeps the id bounds honest through this seam.
        """
        if version_id in self.version_ids:
            raise ValueError(f"asset already references version: {version_id}")
        payload = self.model_dump(mode="python")
        payload["version_ids"] = [*self.version_ids, version_id]
        return Asset.model_validate(payload)


ASSET_VERSION_SCHEMA_VERSION = "workbench.asset-version/1"

# `<algorithm>:<hex digest>`. The algorithm is part of the value on purpose: a
# bare digest forces every reader to guess which hash it is, and a version whose
# checksum cannot be checked is a version that cannot be trusted.
CHECKSUM_PATTERN = r"^[a-z0-9]+:[0-9a-f]{32,128}$"


class AssetVersionContent(BaseModel):
    """Where one version's bytes live, and what they should hash to.

    This is an address plus a digest, never the bytes themselves: the card rules
    out duplicating file bytes, so nothing here can carry a payload.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    location: Annotated[str, Field(min_length=1, max_length=2048)]
    checksum: Annotated[str, Field(pattern=CHECKSUM_PATTERN)]
    mime_type: Annotated[str, Field(min_length=1, max_length=255)]
    size_bytes: Annotated[int, Field(ge=0)]


class AssetVersionProvenance(BaseModel):
    """Where one version came from, speaking the Asset source vocabulary.

    The vocabulary is `AssetSource` itself rather than a parallel copy: two
    closed sets for "where did this enter the project" would drift the first
    time either one gained a member.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    source: AssetSource
    source_ref: Annotated[str, Field(max_length=2048)] | None = None
    actor_id: OpaqueId | None = None


class AssetVersionRef(BaseModel):
    """The address of one version of one asset, and nothing else.

    A ref names identity only. It carries no content, no checksum, no size and
    no time, so it stays valid when the bytes move, are re-hashed or are
    re-described — which is what makes it stable enough to store in a
    Collection cell or an execution input.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    asset_id: OpaqueId
    version_id: OpaqueId


class AssetVersion(BaseModel):
    """One immutable version of one Asset: what it is, where it came from."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal[ASSET_VERSION_SCHEMA_VERSION] = ASSET_VERSION_SCHEMA_VERSION
    id: OpaqueId
    asset_id: OpaqueId
    ordinal: Annotated[int, Field(ge=1)]
    content: AssetVersionContent
    provenance: AssetVersionProvenance
    created_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def freeze_metadata(self) -> "AssetVersion":
        assert_safe_metadata(self.metadata, path="metadata")
        object.__setattr__(self, "metadata", freeze_value(self.metadata))
        return self

    def ref(self) -> AssetVersionRef:
        """The address of this version, derived from identity alone."""
        return AssetVersionRef(asset_id=self.asset_id, version_id=self.id)
