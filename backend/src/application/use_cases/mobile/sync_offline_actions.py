from dataclasses import dataclass
from typing import Any

from backend.src.application.ports.mobile_offline_checkpoint_port import (
    MobileOfflineCheckpointPort,
)


@dataclass
class OfflineSyncResult:
    processed_count: int
    checkpoint: str
    conflict_count: int = 0


class SyncOfflineActionsUseCase:
    def __init__(self, checkpoint_port: MobileOfflineCheckpointPort):
        self._checkpoint_port = checkpoint_port

    def execute(self, device_id: str, pending_actions: list[dict[str, Any]]) -> OfflineSyncResult:
        last_checkpoint = self._checkpoint_port.load_checkpoint(device_id=device_id)
        processed = len(pending_actions)
        checkpoint_base = last_checkpoint if last_checkpoint else "initial"
        next_checkpoint = f"{checkpoint_base}|applied:{processed}"
        self._checkpoint_port.save_checkpoint(device_id=device_id, checkpoint=next_checkpoint)
        return OfflineSyncResult(processed_count=processed, checkpoint=next_checkpoint, conflict_count=0)
