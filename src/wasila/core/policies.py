from __future__ import annotations

from dataclasses import dataclass

from wasila.core.contracts import MemoryUpdate, OwnerNotification, SkillCall
from wasila.core.ports import PolicyEngine


@dataclass
class DefaultPolicyEngine(PolicyEngine):
    """Deterministic policy engine used by the Stage 1 MVP."""

    allowed_memory_sections: set[str] = frozenset(
        {
            "Preferences",
            "Special Handling",
            "Important History",
            "Open Risks",
            "Owner Notes",
        }
    )
    high_risk_signals: tuple[str, ...] = (
        "refund",
        "cancel",
        "churn",
        "angry",
        "escalate",
        "urgent",
        "downtime",
        "breach",
        "complaint",
        "not working",
    )

    def allow_memory_update(self, update: MemoryUpdate) -> bool:
        if not update.section or not update.body.strip():
            return False
        if len(update.body.strip()) > 1800:
            return False
        return update.section in self.allowed_memory_sections

    def allow_skill_execution(self, call: SkillCall) -> bool:
        if call.approval_required:
            return False
        # MVP keeps risky or external actions outside auto-execution.
        return call.execution_level in {"read", "write"}

    def allow_owner_notification(self, notification: OwnerNotification) -> bool:
        if notification.risk_level in {"high", "urgent"}:
            return True
        summary = notification.summary.lower()
        return any(signal in summary for signal in self.high_risk_signals)
