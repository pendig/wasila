from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from typing import Sequence

from wasila.core.contracts import PrivateAgentJob, PrivateAgentResult, private_agent_result_from_json


@dataclass(slots=True)
class CliPrivateAgentAdapter:
    command: Sequence[str]
    timeout_seconds: int = 60

    def run(self, job: PrivateAgentJob) -> PrivateAgentResult:
        if isinstance(self.command, str) or not self.command or not all(isinstance(arg, str) and arg for arg in self.command):
            raise ValueError("private agent command must be a non-empty argument list")
        completed = subprocess.run(
            list(self.command),
            input=json.dumps(job.to_json()),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=self.timeout_seconds,
            check=False,
        )
        if completed.returncode != 0:
            raise ValueError(f"private agent command failed with exit code {completed.returncode}")
        try:
            payload = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            raise ValueError("private agent command returned invalid JSON") from exc
        result = private_agent_result_from_json(payload)
        if result.job_id != job.job_id:
            raise ValueError("private agent result job_id does not match request")
        return result
