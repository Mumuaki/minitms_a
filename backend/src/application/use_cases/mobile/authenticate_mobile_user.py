from dataclasses import dataclass
from typing import Protocol


class SessionBootstrapPort(Protocol):
    def bootstrap_session(self, *, user_id: str, device_id: str) -> str:
        ...


class CredentialVerifierPort(Protocol):
    def verify_credentials(self, *, username: str, password: str) -> bool:
        ...


@dataclass
class MobileAuthResult:
    authenticated: bool
    session_id: str | None = None


class AuthenticateMobileUserUseCase:
    def __init__(
        self,
        session_bootstrap_port: SessionBootstrapPort,
        credential_verifier_port: CredentialVerifierPort,
    ):
        self._session_bootstrap_port = session_bootstrap_port
        self._credential_verifier_port = credential_verifier_port

    def execute(self, username: str, password: str, device_id: str) -> MobileAuthResult:
        if not username or not password or not device_id:
            return MobileAuthResult(authenticated=False)
        if not self._credential_verifier_port.verify_credentials(username=username, password=password):
            return MobileAuthResult(authenticated=False)
        session_id = self._session_bootstrap_port.bootstrap_session(
            user_id=username,
            device_id=device_id,
        )
        return MobileAuthResult(authenticated=True, session_id=session_id)
