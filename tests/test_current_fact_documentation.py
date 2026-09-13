import re
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class CurrentFactDocumentationTests(unittest.TestCase):
    def test_current_status_tracks_local_head_and_active_task_pointer(self):
        status = (ROOT / "docs/status/CURRENT_EXECUTION_STATUS.md").read_text()
        next_task = (ROOT / "AGENT_NEXT_TASK.md").read_text()
        task_index = (ROOT / "docs/tasks/TASK_INDEX.md").read_text()

        head = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip()
        verified_commit = re.search(r'verified_commit: "([0-9a-f]+)', status)
        self.assertIsNotNone(verified_commit)
        self.assertEqual(
            subprocess.run(
                ["git", "merge-base", "--is-ancestor", verified_commit.group(1), head],
                cwd=ROOT,
            ).returncode,
            0,
        )
        self.assertIn("- Active Task: `R9-03`", next_task)
        self.assertRegex(task_index, r"\| `R9-03` \| R9 \| P0 \| ACTIVE \|")


if __name__ == "__main__":
    unittest.main()
