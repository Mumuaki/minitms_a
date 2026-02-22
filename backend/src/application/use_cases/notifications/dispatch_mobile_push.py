from dataclasses import dataclass
from typing import Protocol

from backend.src.application.ports.mobile_push_gateway_port import MobilePushGatewayPort


class CooldownPolicyPort(Protocol):
    def allow_send(self, *, user_id: str) -> bool:
        ...


@dataclass
class MobilePushDispatchResult:
    sent: bool
    message_id: str | None = None


class DispatchMobilePushUseCase:
    def __init__(self, push_gateway_port: MobilePushGatewayPort, cooldown_policy_port: CooldownPolicyPort):
        self._push_gateway_port = push_gateway_port
        self._cooldown_policy_port = cooldown_policy_port

    def execute(self, user_id: str, device_token: str, title: str, body: str) -> MobilePushDispatchResult:
        if not self._cooldown_policy_port.allow_send(user_id=user_id):
            return MobilePushDispatchResult(sent=False)
        message_id = self._push_gateway_port.send(device_token=device_token, title=title, body=body)
        return MobilePushDispatchResult(sent=True, message_id=message_id)
