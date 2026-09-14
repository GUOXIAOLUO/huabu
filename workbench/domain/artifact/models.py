"""Artifact identity for Workbench-produced formal outputs.

An Artifact is the stable identity of one *produced* result: something the
project made by running work, never something brought in from outside. That is
the whole difference from `Asset`, which is the identity of an input. An
Artifact answers *which* output this is — which project produced it, what kind
of formal output it is, what it is called and what state it is in — and nothing
else.

What the output actually *is* at any point belongs to its versions, which are
separate records owned by another card. The Artifact therefore names versions by
id and carries no content, no checksum, no storage location and no lineage: a
reference that also held the payload would give the same fact two owners, and
editing a version would become an edit of the Artifact.

Two absences are deliberate rather than incomplete:

- **No Canvas.** An output is not a card on a board. A node may present an
  Artifact, but the Artifact is defined, validated and persisted without any
  canvas, node, position or renderer — presentation is not identity, and a
  Canvas node that outlives a board must not take the output's identity with it.
- **No approval or frozen lifecycle.** `state` is a placeholder for one, not
  one: which states exist and who may move between them are approval concerns
  owned by a later Round, so this record refuses to answer them yet.
"""

from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from workbench.domain.value_types import OpaqueId, assert_safe_metadata, freeze_value


ARTIFACT_SCHEMA_VERSION = "workbench.artifact/1"

# What kind of formal output one Artifact is. These are the shapes the Workbench
# itself can speak about; `other` is the escape hatch for a kind no Core concept
# names yet, whose specifics belong in `metadata` and in a Package, not in a new
# Core member. No industry kind appears here on purpose.
ArtifactType = Literal[
    "text",
    "analysis",
    "image",
    "video",
    "table",
    "comparison",
    "review",
    "handoff",
    "other",
]

# Placeholder lifecycle state of the identity itself. This is a label, not a
# machine: no transition, approval or freeze is modelled here, and the
# vocabulary deliberately contains no approved/frozen member, because deciding
# those is another Round's authorization concern.
ArtifactState = Literal["draft", "ready", "archived"]


class Artifact(BaseModel):
    """The identity of one produced formal output and the versions it names."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal[ARTIFACT_SCHEMA_VERSION] = ARTIFACT_SCHEMA_VERSION
    id: OpaqueId
    project_id: OpaqueId
    type: ArtifactType
    title: Annotated[str, Field(min_length=1, max_length=500)]
    state: ArtifactState = "draft"
    version_ids: tuple[OpaqueId, ...] = ()
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def require_distinct_version_ids(self) -> "Artifact":
        if len(set(self.version_ids)) != len(self.version_ids):
            raise ValueError("artifact version ids must be unique")
        return self

    @model_validator(mode="after")
    def freeze_metadata(self) -> "Artifact":
        # Same treatment the other canonical records give theirs: a frozen record
        # with a mutable interior is not frozen, and a credential in metadata is
        # a credential in a record that gets persisted and logged.
        assert_safe_metadata(self.metadata, path="metadata")
        object.__setattr__(self, "metadata", freeze_value(self.metadata))
        return self

    def with_version(self, version_id: str) -> "Artifact":
        """Return a new Artifact naming one more version; the identity is unchanged.

        Versions are appended and never rewritten here: a version already named
        by this Artifact stays named by it, and nothing about the version itself
        can be changed through this record. Re-validating the whole record
        (rather than copying it) is what keeps the id and title bounds honest
        through this seam.
        """
        if version_id in self.version_ids:
            raise ValueError(f"artifact already references version: {version_id}")
        payload = self.model_dump(mode="python")
        payload["version_ids"] = [*self.version_ids, version_id]
        return Artifact.model_validate(payload)
