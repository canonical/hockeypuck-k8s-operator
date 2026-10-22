# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

# pylint: disable=protected-access,redefined-outer-name

"""Unit tests for the Hockeypuck charm reconcile and charm state logic."""

from unittest import mock

import ops
import paas_charm.go
import pytest
from requests.exceptions import RequestException

from charm import HockeypuckK8SCharm


@pytest.fixture(name="charm")
def charm_fixture(monkeypatch: pytest.MonkeyPatch):
    """Create a charm instance without running the framework, with a mocked unit.

    Args:
        monkeypatch: pytest monkeypatch fixture.

    Yields:
        The charm instance.
    """
    instance = object.__new__(HockeypuckK8SCharm)
    unit = mock.MagicMock()
    unit.status = ops.ActiveStatus()
    monkeypatch.setattr(HockeypuckK8SCharm, "unit", unit)
    monkeypatch.setattr(HockeypuckK8SCharm, "model", mock.MagicMock())
    monkeypatch.setattr(HockeypuckK8SCharm, "app", mock.MagicMock())
    monkeypatch.setattr(paas_charm.go.Charm, "_reconcile", mock.MagicMock())
    yield instance


@pytest.fixture(name="admin_gpg")
def admin_gpg_fixture():
    """Mock AdminGPG.

    Yields:
        The mocked AdminGPG class.
    """
    with mock.patch("charm.AdminGPG") as admin_gpg_cls:
        yield admin_gpg_cls


def test_reconcile_pushes_key_when_active(charm, admin_gpg):
    """
    arrange: a charm whose parent reconcile leaves the unit active.
    act: run the reconcile.
    assert: the key is pushed after the parent reconcile.
    """
    charm._reconcile()

    admin_gpg.return_value.push_admin_key.assert_called_once_with()


@pytest.mark.parametrize(
    "status",
    [ops.BlockedStatus("blocked"), ops.WaitingStatus("waiting"), ops.MaintenanceStatus("busy")],
)
def test_reconcile_skips_push_when_not_active(charm, admin_gpg, status):
    """
    arrange: a charm whose parent reconcile left the unit in a non-active status.
    act: run the reconcile.
    assert: the admin key is not pushed and the status is untouched.
    """
    charm.unit.status = status

    charm._reconcile()

    admin_gpg.return_value.push_admin_key.assert_not_called()
    assert charm.unit.status == status


def test_reconcile_raises_when_push_fails(charm, admin_gpg, caplog):
    """
    arrange: a charm for which pushing the admin key fails.
    act: run the reconcile.
    assert: the error is logged and raised.
    """
    admin_gpg.return_value.push_admin_key.side_effect = RequestException("boom")

    with pytest.raises(RequestException):
        charm._reconcile()

    assert "Unable to push admin key to Hockeypuck" in caplog.text


@pytest.mark.parametrize(
    "user_keys, expected",
    [
        pytest.param(None, "FINGERPRINT", id="no user keys"),
        pytest.param("AAA,BBB", "AAA,BBB,FINGERPRINT", id="user keys"),
        pytest.param("AAA,", "AAA,FINGERPRINT", id="trailing comma"),
    ],
)
def test_create_charm_state_adds_admin_fingerprint(
    charm, admin_gpg, monkeypatch, user_keys, expected
):
    """
    arrange: a charm state with or without user defined admin keys.
    act: create the charm state.
    assert: the admin fingerprint is appended to the admin keys.
    """
    config = {} if user_keys is None else {"admin_keys": user_keys}
    charm_state = mock.MagicMock()
    charm_state.user_defined_config = config
    monkeypatch.setattr(
        paas_charm.go.Charm, "_create_charm_state", mock.MagicMock(return_value=charm_state)
    )
    admin_gpg.return_value.admin_fingerprint.return_value = "FINGERPRINT"

    result = charm._create_charm_state()

    assert result.user_defined_config["admin_keys"] == expected


def test_is_ready_blocks_multi_unit(charm):
    """
    arrange: a charm planned with two units.
    act: check readiness.
    assert: the charm is not ready and the unit is blocked.
    """
    charm.model.app.planned_units.return_value = 2
    charm.unit.is_leader.return_value = False

    assert not charm.is_ready()
    assert isinstance(charm.unit.status, ops.BlockedStatus)
