from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from typing import Sequence

from wasila.core.contracts import (
    PrivateAgentJob,
    PrivateAgentResult,
    private_agent_job_from_json,
    private_agent_result_from_json,
)


@dataclass(slots=True)
class CliPrivateAgentAdapter:
    command: Sequence[str]
    timeout_seconds: int = 60

    def run(self, job: PrivateAgentJob) -> PrivateAgentResult:
        if (
            isinstance(self.command, str)
            or not self.command
            or not all(isinstance(arg, str) and arg for arg in self.command)
        ):
            raise ValueError("private agent command must be a non-empty argument list")

        safe_job = private_agent_job_from_json(job.to_json())
        try:
            completed = subprocess.run(  # noqa: S603 - command is explicit args only.
                list(self.command),
                input=json.dumps(safe_job.to_json()),
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=self.timeout_seconds,
                check=False,
                env={"PATH": os.environ.get("PATH", "")},
            )
        except subprocess.TimeoutExpired as exc:
            raise ValueError("private agent command timed out") from exc
        except OSError as exc:
            raise ValueError("private agent command could not be executed") from exc

        if completed.returncode != 0:
            stderr = completed.stderr.strip()
            detail = f": {stderr}" if stderr else ""
            raise ValueError(
                "private agent command failed with "
                f"exit code {completed.returncode}{detail}"
            )
        try:
            payload = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            preview = completed.stdout[:100]
            if len(completed.stdout) > 100:
                preview += "..."
            raise ValueError(
                f"private agent command returned invalid JSON: {preview!r}"
            ) from exc
        result = private_agent_result_from_json(payload)
        if result.job_id != job.job_id:
            raise ValueError("private agent result job_id does not match request")
        return result
