from typing import Protocol


class MobileOfflineCheckpointPort(Protocol):
    def load_checkpoint(self, *, device_id: str) -> str | None:
        ...

    def save_checkpoint(self, *, device_id: str, checkpoint: str) -> None:
        ...
