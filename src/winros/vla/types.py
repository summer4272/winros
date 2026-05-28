from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol


@dataclass(frozen=True)
class VLARequest:
    instruction: str
    robot: str
    image_path: Path | None = None
    context: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class StructuredCommand:
    robot: str
    command_type: str
    target: dict[str, Any]
    dry_run: bool = True
    source_provider: str = "unknown"
    confidence: float = 0.0
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "robot": self.robot,
            "command_type": self.command_type,
            "target": self.target,
            "dry_run": self.dry_run,
            "source_provider": self.source_provider,
            "confidence": self.confidence,
            "notes": list(self.notes),
        }


class VLAProvider(Protocol):
    name: str
    description: str

    def generate(self, request: VLARequest) -> StructuredCommand:
        """Return a validated, structured dry-run robot command."""
