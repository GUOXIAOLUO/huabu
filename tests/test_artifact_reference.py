import unittest

from workbench.application.artifact_reference import ArtifactVersionReferenceValidator


class ArtifactReferenceTests(unittest.TestCase):
    def test_validates_project_and_version_identity(self):
        class Artifact:
            project_id = "project-1"

        class Version:
            id = "version-1"
            artifact_id = "artifact-1"

        class Reader:
            def get(self, artifact_id):
                self.artifact_id = artifact_id
                return Artifact()

            def list_versions(self, artifact_id):
                return [Version()]

        ArtifactVersionReferenceValidator(Reader()).validate(
            actor_id="owner", project_id="project-1",
            reference={"artifact_id": "artifact-1", "version_id": "version-1"},
        )

    def test_rejects_cross_project_and_unknown_version(self):
        class Artifact:
            project_id = "project-2"

        class Reader:
            def get(self, artifact_id):
                return Artifact()

            def list_versions(self, artifact_id):
                return []

        validator = ArtifactVersionReferenceValidator(Reader())
        with self.assertRaises(PermissionError):
            validator.validate(actor_id="owner", project_id="project-1", reference={"artifact_id": "a", "version_id": "v"})

    def test_maps_missing_artifact_to_reference_lookup_error(self):
        class Reader:
            def get(self, artifact_id):
                from workbench.repositories.artifact_repository import ArtifactNotFoundError
                raise ArtifactNotFoundError(artifact_id)

            def list_versions(self, artifact_id):
                return []

        with self.assertRaises(LookupError):
            ArtifactVersionReferenceValidator(Reader()).validate(
                actor_id="owner", project_id="project-1", reference={"artifact_id": "missing", "version_id": "v"}
            )


if __name__ == "__main__":
    unittest.main()
