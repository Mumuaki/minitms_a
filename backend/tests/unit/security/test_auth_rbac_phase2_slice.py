import pytest

from backend.src.application.use_cases.auth.login_user import LoginUserUseCase
from backend.src.domain.entities.user import User, UserRole
from backend.src.infrastructure.security.password_hasher import hash_password
from backend.src.infrastructure.security.rbac import Permission, has_permission


class StubUserRepo:
    def __init__(self, user: User | None):
        self._user = user
        self.updated = False

    def get_by_email(self, email: str):
        if self._user and self._user.email == email:
            return self._user
        return None

    def get_by_id(self, user_id: int):
        if self._user and self._user.id == user_id:
            return self._user
        return None

    def update(self, user: User) -> None:
        self.updated = True
        self._user = user


@pytest.mark.requirement_id("FR-AUTH-001")
@pytest.mark.test_id("TST-FR-AUTH-001-WEB-AT")
def test_fr_auth_001_web_login_success_returns_tokens():
    user = User(
        email="dispatcher@mini.tms",
        username="dispatcher",
        password_hash=hash_password("secret"),
        role=UserRole.DISPATCHER,
        language="en",
        is_active=True,
    )
    user.id = 101
    repo = StubUserRepo(user)

    result = LoginUserUseCase(repo).execute(
        email="dispatcher@mini.tms",
        password="secret",
        remember_me=True,
    )

    assert result.success is True
    assert result.user_id == 101
    assert result.role == "dispatcher"
    assert result.access_token
    assert result.refresh_token
    assert repo.updated is True


@pytest.mark.requirement_id("FR-AUTH-002")
@pytest.mark.test_id("TST-FR-AUTH-002-WEB-AT")
def test_fr_auth_002_web_rbac_matrix_core_permissions():
    assert has_permission("administrator", Permission.USER_CREATE) is True
    assert has_permission("director", Permission.SETTINGS_UPDATE) is True
    assert has_permission("dispatcher", Permission.CARGO_SEARCH) is True
    assert has_permission("observer", Permission.EMAIL_SEND) is False


@pytest.mark.requirement_id("FR-AUTH-002")
@pytest.mark.test_id("TST-FR-AUTH-002-WEB-INTEG")
def test_fr_auth_002_web_guest_alias_is_observer():
    assert has_permission("guest", Permission.CARGO_READ) is True
    assert has_permission("guest", Permission.REPORT_READ) is True
    assert has_permission("guest", Permission.EMAIL_SEND) is False


@pytest.mark.requirement_id("FR-AUTH-002")
@pytest.mark.test_id("TST-FR-AUTH-002-WEB-UNIT-INVALID-ROLE")
def test_fr_auth_002_web_invalid_role_input_is_safe():
    assert has_permission("", Permission.CARGO_READ) is False
    assert has_permission(None, Permission.CARGO_READ) is False
