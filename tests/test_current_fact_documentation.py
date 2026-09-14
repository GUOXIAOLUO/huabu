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
        active = re.search(r"- Active Task: `([^`]+)`", next_task)
        self.assertIsNotNone(active)
        self.assertRegex(task_index, rf"\| `{active.group(1)}` \| [^|]+ \| [^|]+ \| ACTIVE \|")
        self.assertEqual(len(re.findall(r"\| [^|]+ \| [^|]+ \| [^|]+ \| ACTIVE \|", task_index)), 1)
        self.assertRegex(task_index, r"\| `R9-11` \| R9 \| P1 \| DONE \|")

    def test_active_task_pointer_status_does_not_contradict_the_card(self):
        # `AGENT_NEXT_TASK.md` was left reading "implementation not started" while
        # the card it pointed at said the implementation was complete, because
        # only the `- Active Task:` line was pinned. Pin the *relationship*
        # instead of the literal, so the same drift cannot recur on the next card.
        next_task = (ROOT / "AGENT_NEXT_TASK.md").read_text()
        pointer_status = re.search(r"- Status: `([^`]*)`", next_task)
        card_reference = re.search(r"- Task Card: `([^`]+)`", next_task)
        self.assertIsNotNone(pointer_status, "the pointer must declare a Status")
        self.assertIsNotNone(card_reference, "the pointer must name its task card")

        card = (ROOT / card_reference.group(1)).read_text()
        card_status = re.search(r"^- Status: (.+)$", card, re.M)
        self.assertIsNotNone(card_status, "the active card must declare a Status")

        implemented = "implementation complete" in card_status.group(1)
        self.assertEqual(
            "not started" in pointer_status.group(1),
            not implemented,
            "AGENT_NEXT_TASK.md must not call the active card unstarted once it is implemented",
        )


if __name__ == "__main__":
    unittest.main()
