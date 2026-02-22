from typing import Protocol


class MobilePushGatewayPort(Protocol):
    def send(self, *, device_token: str, title: str, body: str) -> str:
        ...
