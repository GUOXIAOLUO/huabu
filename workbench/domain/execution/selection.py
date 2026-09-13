"""Immutable per-result user preference metadata.

A result is identified by the attempt that produced it together with the output
name and that output's occurrence in the attempt's batch — the same identity the
Result Tray stages and the Result Compare workspace compares. This record is the
canonical home for what the *user* decided about a result.

Two boundaries are deliberate. The rating is what a user assigned: nothing here
is computed, ranked, scored or derived, so this record can never become a
machine judgement about which candidate is better. And no approval or frozen
state is modelled: freezing a design belongs to a later, separate concept, so
this record stays a preference rather than an authorization.
"""

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from workbench.domain.value_types import OpaqueId, assert_safe_metadata, freeze_value


EXECUTION_RESULT_SELECTION_SCHEMA_VERSION = "workbench.result-selection/1"
RESULT_SELECTION_MIN_RATING = 1
RESULT_SELECTION_MAX_RATING = 5
RESULT_SELECTION_MAX_COMMENT_LENGTH = 2000


class ResultSelection(BaseModel):
    """User preference metadata for one run result."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal[EXECUTION_RESULT_SELECTION_SCHEMA_VERSION] = EXECUTION_RESULT_SELECTION_SCHEMA_VERSION
    id: OpaqueId
    run_id: OpaqueId
    attempt_id: OpaqueId
    output_name: Annotated[str, Field(min_length=1, max_length=255)]
    ordinal: Annotated[int, Field(ge=0)]
    selected: bool = False
    favorite: bool = False
    rating: Annotated[int, Field(ge=RESULT_SELECTION_MIN_RATING, le=RESULT_SELECTION_MAX_RATING)] | None = None
    comment: Annotated[str, Field(max_length=RESULT_SELECTION_MAX_COMMENT_LENGTH)] = ""
    created_at: datetime
    updated_at: datetime | None = None
    metadata: dict[str, object] = Field(default_factory=dict)
    revision: Annotated[int, Field(ge=1)] = 1

    @model_validator(mode="after")
    def validate_metadata(self):
        assert_safe_metadata(self.metadata, path="metadata")
        object.__setattr__(self, "metadata", freeze_value(self.metadata))
        return self

    def has_preference(self) -> bool:
        """True when the user expressed anything at all about this result."""
        return self.selected or self.favorite or self.rating is not None or bool(self.comment.strip())
