import unittest

from pydantic import ValidationError

from workbench.domain.provider import (
    CREDENTIAL_REF_SCHEMA_VERSION,
    PROVIDER_CONNECTION_SCHEMA_VERSION,
    CredentialRef,
    ProviderConnection,
)


class ProviderConnectionTests(unittest.TestCase):
    def test_multiple_connections_share_provider_without_sharing_secret_values(self):
        first = ProviderConnection(
            id="openai-primary",
            provider_id="generic.openai-compatible",
            ref="account-primary",
            config={"base_url": "https://primary.example.invalid"},
            credential_ref=CredentialRef(id="credential-primary"),
            status="active",
        )
        second = ProviderConnection(
            id="openai-secondary",
            provider_id=first.provider_id,
            ref="account-secondary",
            config={"base_url": "https://secondary.example.invalid"},
            credential_ref=CredentialRef(id="credential-secondary"),
            status="disabled",
        )

        self.assertEqual(first.schema_version, PROVIDER_CONNECTION_SCHEMA_VERSION)
        self.assertEqual(first.credential_ref.schema_version, CREDENTIAL_REF_SCHEMA_VERSION)
        self.assertEqual((first.provider_id, second.provider_id), (first.provider_id,) * 2)
        self.assertNotEqual(first.id, second.id)
        self.assertEqual(first.model_dump(mode="json")["credential_ref"]["id"], "credential-primary")
        self.assertNotIn("secret", str(first.model_dump(mode="json")))

    def test_connection_rejects_secret_fields_and_is_immutable(self):
        connection = ProviderConnection(id="connection", provider_id="provider", ref="account")

        with self.assertRaises(ValidationError):
            CredentialRef(id="credential", secret="must-not-be-stored")
        with self.assertRaises(ValidationError):
            ProviderConnection(
                id="connection",
                provider_id="provider",
                ref="account",
                config={"nested": {"api_key": "must-not-be-stored"}},
            )
        with self.assertRaises(ValidationError):
            ProviderConnection(
                id="connection",
                provider_id="provider",
                ref="account",
                metadata={"apiKey": "must-not-be-stored"},
            )
        with self.assertRaises(ValidationError):
            connection.status = "active"


if __name__ == "__main__":
    unittest.main()
