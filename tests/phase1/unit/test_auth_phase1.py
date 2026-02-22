import pytest

from phase1.auth import AuthService
from phase1.models import ALLOWED_ROLES, User

@pytest.mark.requirement_id("FR-AUTH-001")
@pytest.mark.test_id("TST-FR-AUTH-001-UNIT")
def test_fr_auth_001_login_with_valid_credentials(sample_user, now):
    service = AuthService([sample_user])
    session = service.login("dispatcher", "secret", now)
    assert session.username == "dispatcher"
    assert session.role == "Dispatcher"


@pytest.mark.requirement_id("FR-AUTH-002")
@pytest.mark.test_id("TST-FR-AUTH-002-UNIT")
def test_fr_auth_002_role_matrix_has_four_roles():
    expected = {"Administrator", "Director", "Dispatcher", "Observer"}
    assert expected.issubset(ALLOWED_ROLES)
    service = AuthService([User(username="guest", password="p", role="Guest")])
    assert service.canonical_role("Guest") == "Observer"
    assert service.canonical_role("Observer") == "Observer"


@pytest.mark.requirement_id("FR-AUTH-004")
@pytest.mark.test_id("TST-FR-AUTH-004-UNIT")
def test_fr_auth_004_remember_me_token_ttl_30_days(sample_user, now):
    service = AuthService([sample_user, User(username="admin", password="p", role="Administrator")])
    session = service.login("dispatcher", "secret", now, remember_me=True)
    assert (session.remember_me_expires_at - now).days == 30
