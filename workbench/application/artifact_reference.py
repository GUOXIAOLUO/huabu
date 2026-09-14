"""Application validation for Canvas references to canonical ArtifactVersions."""

from typing import Protocol

from workbench.repositories.artifact_repository import ArtifactNotFoundError


class ArtifactVersionReader(Protocol):
    def get(self, artifact_id: str) -> object: ...
    def list_versions(self, artifact_id: str) -> list[object]: ...


class ArtifactVersionReferenceValidator:
    """Validates ArtifactVersion identity and project scope before node creation."""

    def __init__(self, artifacts: ArtifactVersionReader):
        self._artifacts = artifacts

    def validate(self, *, actor_id: str, project_id: str, reference: dict) -> None:
        if not isinstance(reference, dict):
            raise ValueError("artifact version reference must be an object")
        artifact_id = str(reference.get("artifact_id") or "").strip()
        version_id = str(reference.get("version_id") or "").strip()
        if not artifact_id or not version_id:
            raise ValueError("artifact version reference requires artifact and version ids")
        try:
            artifact = self._artifacts.get(artifact_id)
        except ArtifactNotFoundError as error:
            raise LookupError("artifact not found") from error
        if artifact.project_id != project_id:
            raise PermissionError("artifact belongs to another project")
        try:
            versions = self._artifacts.list_versions(artifact_id)
        except ArtifactNotFoundError as error:
            raise LookupError("artifact version not found") from error
        if not any(version.id == version_id and version.artifact_id == artifact_id for version in versions):
            raise LookupError("artifact version not found")
