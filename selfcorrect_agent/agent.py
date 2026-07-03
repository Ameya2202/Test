"""The self-correcting agent loop.

Implements the PRD's bounded state machine:

    Generate -> Run -> Diagnose -> Correct / Escalate / Quarantine -> Verify -> Stop

It never modifies your file on its own. `run()` returns a Session describing the
proposed change and the full cycle; applying it is a separate, explicit step
(see server.apply_session / Session.apply), so a human is always in the loop.
"""
from __future__ import annotations

import difflib
import shutil
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from .config import Config
from .providers import get_provider
from .sandbox import run_pytest


@dataclass
class Step:
    name: str          # Generate | Run | Diagnose | Correct | Quarantine | Verify | Stop
    status: str        # ok | fail | warn | info
    detail: str
    attempt: int = 0
    ts: float = field(default_factory=time.time)


@dataclass
class Session:
    id: str
    file_path: str
    original_code: str
    improved_code: str
    tests_code: str
    rationale: str
    steps: List[Step]
    status: str                       # ready | escalate | error
    attempts_used: int
    final_summary: str
    before_score: float = 0.0
    after_score: float = 0.0
    baseline_summary: str = ""
    verified_summary: str = ""
    applied: bool = False
    backup_path: Optional[str] = None
    test_path: Optional[str] = None

    @property
    def changed(self) -> bool:
        return self.improved_code.strip() != self.original_code.strip()

    @property
    def unified_diff(self) -> str:
        return "".join(
            difflib.unified_diff(
                self.original_code.splitlines(keepends=True),
                self.improved_code.splitlines(keepends=True),
                fromfile=f"a/{Path(self.file_path).name}",
                tofile=f"b/{Path(self.file_path).name}",
            )
        )

    @property
    def improvement_percent(self) -> float:
        """Percentage-point improvement from the original to the final candidate."""
        return round(self.after_score - self.before_score, 1)

    def apply(self, write_tests: bool = True) -> None:
        """Write the improved code to the real file (with a timestamped backup).

        This is the only place the agent touches your production file, and it is
        only ever called after explicit human approval.
        """
        target = Path(self.file_path)
        stamp = time.strftime("%Y%m%d-%H%M%S")
        backup = target.with_suffix(target.suffix + f".bak.{stamp}")
        shutil.copy2(target, backup)
        target.write_text(self.improved_code, encoding="utf-8")
        self.backup_path = str(backup)
        if write_tests:
            test_file = target.parent / f"test_{target.stem}.py"
            # rewrite the import to match the real module name
            body = self.tests_code.replace(
                "from solution import", f"from {target.stem} import"
            )
            test_file.write_text(body, encoding="utf-8")
            self.test_path = str(test_file)
        self.applied = True


class SelfCorrectingAgent:
    def __init__(self, config: Optional[Config] = None, provider=None):
        self.config = config or Config()
        self.provider = provider or get_provider(self.config)

    def run(self, file_path: str) -> Session:
        path = Path(file_path)
        original = path.read_text(encoding="utf-8")
        steps: List[Step] = []
        sid = uuid.uuid4().hex[:12]

        # 1. Generate
        proposal = self.provider.propose(path.name, original)
        improved, tests = proposal.improved_code, proposal.tests_code
        steps.append(Step("Generate", "ok",
                          "Author proposed an improved module and a pytest suite.", 1))

        status = "escalate"
        attempt = 0
        last_summary = ""
        for attempt in range(1, self.config.max_attempts + 1):
            # 2. Run
            result = run_pytest(improved, tests, self.config.test_timeout)
            last_summary = result.summary
            steps.append(Step("Run", "ok" if result.passed else "fail",
                              result.summary, attempt))

            if result.passed:
                # 5. Verify
                steps.append(Step("Verify", "ok",
                                  "Suite is green and assertions still pin the behaviour.",
                                  attempt))
                status = "ready"
                break

            # 3. Diagnose
            diag = self.provider.diagnose(improved, tests, result.output)
            steps.append(Step("Diagnose", "info",
                              f"{diag.classification}: {diag.explanation}", attempt))

            # 4c. Quarantine (environmental)
            if diag.classification == "environmental":
                steps.append(Step("Quarantine", "warn",
                                  "Environmental failure; retrying once.", attempt))
                continue

            # 4a/4b. Correct (bad_test) or fix code (bad_code)
            rev = self.provider.revise(improved, tests, result.output, diag.classification)
            improved, tests = rev.improved_code, rev.tests_code
            steps.append(Step("Correct", "ok",
                              f"{diag.classification} corrected: {rev.note}", attempt))
        else:
            # 6. Stop — budget exhausted
            steps.append(Step("Stop", "fail",
                              f"Attempt budget ({self.config.max_attempts}) exhausted; "
                              "escalating to a human.", attempt))

        baseline = run_pytest(original, tests, self.config.test_timeout)
        verified = run_pytest(improved, tests, self.config.test_timeout)
        steps.append(Step(
            "Score",
            "ok" if verified.pass_rate >= baseline.pass_rate else "warn",
            (
                f"Original scored {baseline.pass_rate}% ({baseline.summary}); "
                f"candidate scored {verified.pass_rate}% ({verified.summary})."
            ),
            attempt,
        ))

        return Session(
            id=sid,
            file_path=str(path.resolve()),
            original_code=original,
            improved_code=improved,
            tests_code=tests,
            rationale=proposal.rationale,
            steps=steps,
            status=status,
            attempts_used=attempt,
            final_summary=last_summary,
            before_score=baseline.pass_rate,
            after_score=verified.pass_rate,
            baseline_summary=baseline.summary,
            verified_summary=verified.summary,
        )
