"""Behavioral tests for the single installed-Skill discovery boundary."""

import unittest

from workbench.application.skill_registry import (
    SkillRegistration,
    SkillPackRegistration,
    SkillRegistry,
    SkillRegistryError,
)
from workbench.domain.skill import SkillDefinition, SkillPack, SkillPackageRef, SkillRef


class SkillRegistryTests(unittest.TestCase):
    @staticmethod
    def skill(skill_id="common.image-analysis", version="1.0.0", title="Image analysis"):
        return SkillDefinition(
            id=skill_id,
            version=version,
            title=title,
            package=SkillPackageRef(package_id="workbench.common", version="1.0.0"),
        )

    def registration(self, skill_id="common.image-analysis", version="1.0.0", title="Image analysis", source="package", source_id="common"):
        skill = self.skill(skill_id, version, title)
        if source == "system":
            skill = skill.model_copy(update={"package": None})
        return SkillRegistration(
            skill=skill, source=source, source_id=source_id, tags=("vision", "analysis")
        )

    def pack_registration(self, pack_id="common-pack", version="1.0.0", enabled=True):
        return SkillPackRegistration(
            pack=SkillPack(
                id=pack_id,
                version=version,
                title="Common Skills",
                package={"package_id": "workbench.common", "version": version},
                skills=(SkillRef(skill_id="common.image-analysis", version="1.0.0"),),
                enabled=enabled,
            ),
            source="package",
            source_id="common",
        )

    def test_register_list_search_and_exact_version_resolution(self):
        registry = SkillRegistry([
            self.registration(version="1.0.0", title="Image analysis"),
            self.registration(version="2.0.0", title="Image analysis v2"),
            self.registration(skill_id="common.text-summary", title="Text summary", source="system", source_id="core"),
        ])

        self.assertEqual([item.skill.version for item in registry.list(package_id="workbench.common")], ["1.0.0", "2.0.0"])
        self.assertEqual([item.skill.id for item in registry.search("summary")], ["common.text-summary"])
        self.assertEqual(registry.search("VISION", source="package")[0].skill.version, "1.0.0")
        self.assertEqual(registry.resolve("common.image-analysis", "2.0.0").skill.version, "2.0.0")
        self.assertIsNone(registry.resolve("common.image-analysis", "3.0.0"))

    def test_discover_is_the_single_future_caller_entrypoint(self):
        registry = SkillRegistry([self.registration()])

        discovered = registry.discover(query="analysis", source="package")

        self.assertEqual(len(discovered), 1)
        self.assertEqual(discovered[0].source_id, "common")
        self.assertEqual(discovered[0].skill.package.package_id, "workbench.common")

    def test_duplicate_registration_and_missing_exact_version_are_explicit(self):
        registry = SkillRegistry([self.registration()])

        with self.assertRaisesRegex(SkillRegistryError, "already registered"):
            registry.register(self.registration())
        with self.assertRaisesRegex(SkillRegistryError, "not registered"):
            registry.require("common.image-analysis", "9.0.0")

    def test_unregister_removes_only_the_exact_version(self):
        registry = SkillRegistry([self.registration(), self.registration(version="2.0.0")])

        removed = registry.unregister("common.image-analysis", "1.0.0")

        self.assertEqual(removed.skill.version, "1.0.0")
        self.assertIsNone(registry.resolve("common.image-analysis", "1.0.0"))
        self.assertIsNotNone(registry.resolve("common.image-analysis", "2.0.0"))
        self.assertIsNone(registry.unregister("common.image-analysis", "9.0.0"))

    def test_pack_associations_and_registry_level_enablement_control_discovery(self):
        registry = SkillRegistry([self.registration()], [self.pack_registration()])

        self.assertEqual(len(registry.list_packs(enabled=True)), 1)
        self.assertEqual(len(registry.list()), 1)
        registry.set_pack_enabled("common-pack", "1.0.0", False)
        self.assertEqual(registry.list(), [])
        self.assertEqual(len(registry.list(include_disabled=True)), 1)
        self.assertFalse(registry.resolve_pack("common-pack", "1.0.0").pack.enabled)
        self.assertEqual(registry.list_packs(enabled=False)[0].pack.skills[0], SkillRef(skill_id="common.image-analysis", version="1.0.0"))
        registry.set_pack_enabled("common-pack", "1.0.0", True)
        self.assertIsNotNone(registry.resolve("common.image-analysis", "1.0.0"))

    def test_pack_references_and_pack_versions_are_exact(self):
        with self.assertRaisesRegex(ValueError, "references must be unique"):
            SkillPack(
                id="pack", version="1", title="Pack",
                skills=(SkillRef(skill_id="skill", version="1"), SkillRef(skill_id="skill", version="1")),
            )
        registry = SkillRegistry(packs=[self.pack_registration(version="2.0.0")])
        self.assertIsNone(registry.resolve_pack("common-pack", "1.0.0"))
        with self.assertRaisesRegex(SkillRegistryError, "not registered"):
            registry.set_pack_enabled("common-pack", "1.0.0", False)


if __name__ == "__main__":
    unittest.main()
